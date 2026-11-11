using JuMP, SCS, JSON3, LinearAlgebra, Pkg

# Environment test only: min <C,X>, X >= 0, diag(X)=1 has optimum 0 at X=ones(2,2).
BLAS.set_num_threads(1)
input = JSON3.read(read(ARGS[1], String))
A = reduce(vcat, [permutedims(Float64.(row)) for row in input.matrix])
product = A * Float64.(input.vector)
C = [1.0 -1.0; -1.0 1.0]
model = Model(SCS.Optimizer)
set_silent(model)
set_optimizer_attribute(model, "eps_abs", 1e-7)
set_optimizer_attribute(model, "eps_rel", 1e-7)
set_optimizer_attribute(model, "max_iters", 10000)
set_optimizer_attribute(model, "time_limit_secs", 15.0)
@variable(model, X[1:2, 1:2], PSD)
@constraint(model, diagonal[i=1:2], X[i, i] == 1.0)
@objective(model, Min, sum(C .* X))
optimize!(model)
@assert termination_status(model) == JuMP.MOI.OPTIMAL
Xv = value.(X)
objective = objective_value(model)
recomputed = sum(C .* Xv)
@assert abs(objective) < 1e-5
@assert abs(recomputed - objective) < 1e-10
@assert maximum(abs.(diag(Xv) .- 1.0)) < 1e-5
@assert minimum(eigvals(Symmetric(Xv))) > -1e-5
@assert maximum(abs.(Xv .- ones(2, 2))) < 1e-5
packages = Dict(p.name => string(p.version) for p in values(Pkg.dependencies()) if p.version !== nothing)
report = Dict(
    "status" => "passed",
    "scope" => "known-answer environment smoke test; not the UAV benchmark or a rigorous certificate",
    "julia" => string(VERSION),
    "julia_threads" => Threads.nthreads(),
    "blas_threads" => BLAS.get_num_threads(),
    "blas_backend" => string(BLAS.get_config()),
    "packages" => packages,
    "matrix_vector_product" => product,
    "objective" => objective,
    "objective_recomputed" => recomputed,
    "primal_diagonal_error" => maximum(abs.(diag(Xv) .- 1.0)),
    "minimum_eigenvalue" => minimum(eigvals(Symmetric(Xv))),
    "termination_status" => string(termination_status(model)),
    "solver_seconds" => solve_time(model),
)
write(ARGS[2], JSON3.write(report))
