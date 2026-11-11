using JuMP, SCS, JSON3, LinearAlgebra
BLAS.set_num_threads(1)
matrix(rows) = reduce(vcat, [permutedims(Float64.(r)) for r in rows])
rows(A) = [collect(A[i, :]) for i in axes(A, 1)]

# 4 times the scalar-first quaternion moment matrix; equivalent by congruence
# to the published ICCV2025 conv(SO(3)) LMI. No SfM objective is reused.
function hull(Y)
    a,b,c = Y[1,1],Y[2,2],Y[3,3]
    return [1+a+b+c Y[3,2]-Y[2,3] Y[1,3]-Y[3,1] Y[2,1]-Y[1,2];
            Y[3,2]-Y[2,3] 1+a-b-c Y[1,2]+Y[2,1] Y[1,3]+Y[3,1];
            Y[1,3]-Y[3,1] Y[1,2]+Y[2,1] 1-a+b-c Y[2,3]+Y[3,2];
            Y[2,1]-Y[1,2] Y[1,3]+Y[3,1] Y[2,3]+Y[3,2] 1-a-b+c]
end

function solve_request(q)
    started = time_ns()
    n = Int(q.n); d = 3*n
    M = zeros(d,d)
    # Rebuild independently from raw endpoint directions, not Python's matrix.
    for o in q.observations
        i, j = 3*Int(o.i)+1:3*Int(o.i)+3, 3*Int(o.j)+1:3*Int(o.j)+3
        a,b = Float64.(o.gi),Float64.(o.gj)
        M[i,i] += a*a'; M[j,j] += b*b'
        M[i,j] += a*b'; M[j,i] += b*a'
    end
    model = Model(SCS.Optimizer); set_silent(model)
    for key in ["eps_abs","eps_rel","eps_infeas","max_iters","time_limit_secs"]
        set_optimizer_attribute(model,key,getproperty(q.settings,Symbol(key)))
    end
    @variable(model, X[1:d,1:d], PSD)
    diagonal_constraints = []
    for i in 0:n-1, a in 1:3, b in a:3
        c = @constraint(model, X[3*i+a,3*i+b] == (a==b ? 1.0 : 0.0))
        push!(diagonal_constraints,(i,a,b,c))
    end
    hull_constraints = []
    for edge in q.strengthened
        i,j = Int(edge[1]),Int(edge[2])
        H = hull(X[3*i+1:3*i+3,3*j+1:3*j+3])
        c = @constraint(model, Symmetric(H) in PSDCone())
        push!(hull_constraints,c)
    end
    @objective(model, Min, sum(M .* X))
    optimize!(model)
    report = Dict{String,Any}("id"=>q.id,"method"=>q.method,"input_sha256"=>q.input_sha256,
        "termination"=>string(termination_status(model)),"solver_seconds"=>solve_time(model),
        "wall_seconds"=>(time_ns()-started)/1e9,"strengthened"=>q.strengthened,"M"=>rows(M))
    if has_values(model) && has_duals(model)
        Lambda = zeros(d,d)
        for (i,a,b,c) in diagonal_constraints
            val = dual(c)/(a==b ? 1.0 : 2.0)
            Lambda[3*i+a,3*i+b]=val; Lambda[3*i+b,3*i+a]=val
        end
        report["X"] = rows(value.(X)); report["Lambda"] = rows(Lambda)
        report["Z"] = [rows(Matrix(dual(c))) for c in hull_constraints]
        report["S"] = rows(Matrix(dual(VariableInSetRef(X))))
        report["objective"] = objective_value(model)
        report["dual_objective"] = dual_objective_value(model)
    end
    return report
end

# One long-lived Julia process: startup/JIT is recorded separately by the caller.
for line in eachline(stdin)
    try
        println(JSON3.write(solve_request(JSON3.read(line)))); flush(stdout)
    catch err
        println(JSON3.write(Dict("error"=>sprint(showerror,err)))); flush(stdout)
    end
end
