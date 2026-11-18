#!/usr/bin/env python3
"""Current task/repair kernel over an immutable scientific executor snapshot."""
import ast
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import hashlib

HERE=Path(__file__).resolve().parent


def check_pin(pin):
    root=Path(pin['code_root']).resolve();index=Path(pin['index']['path'])
    if hashlib.sha256(index.read_bytes()).hexdigest()!=pin['index']['sha256']:
        raise ValueError('独立执行端版本索引不匹配')
    for name,digest in json.loads(index.read_text())['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('独立执行端代码发生漂移：'+name)
    return root


def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def install(root):
    sys.path.insert(0,str(root))
    # The current recovery controller requires the current continuation API.
    # Replace even a cached legacy module before installing recovery consumers;
    # evidence readers and scientific validators still resolve from the pin.
    load('research_continuation')
    monitor=load('experiment_monitor')
    verification_monitor=load('verification_monitor')
    task_trace=load('task_trace')
    features=load('platform_features')
    prose=load('manuscript_quality')
    routing=load('model_routing')
    load('token_audit')
    load('usage_ledger')
    load('token_usage')
    revision=load('runtime_revision');autonomy=load('autonomy');repair=load('code_repair');self_repair=load('self_repair')
    import ars
    ars.paper_workflow.manuscript_quality=prose
    ars.runtime_revision=revision;ars.autonomy=autonomy;ars.code_repair=repair;ars.self_repair=self_repair
    ars.PHASES.add(repair.PHASE)
    ars.PHASE_LABELS[repair.PHASE]='自动调用agent修复代码与复验'
    original_context=ars.assemble_context;original_verify=ars.verify_task_result
    original_accept=ars.accept_task_result;original_argv=ars.executor_argv;original_advance=ars.advance
    original_reserve=ars.reserve_task;original_start=ars.start_campaign
    # Borrow only engineering control functions. All scientific modules,
    # verifiers, source/config bindings and the saved runtime pin remain intact.
    import local_extensions
    tree=ast.parse(local_extensions.source(HERE/'ars.py'))
    names={'assemble_context','verify_task_result','accept_task_result','executor_argv',
           'finalize_operation','execute_activity','run_campaign','stop_campaign','public_state','progress_state'}
    nodes=[node for node in tree.body if isinstance(node,ast.Import)
           or (isinstance(node,ast.ImportFrom) and node.module!='__future__')
           or (isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(HERE/'ars.py'),'exec'),ars.__dict__)
    new_context=ars.assemble_context;new_verify=ars.verify_task_result;new_accept=ars.accept_task_result;new_argv=ars.executor_argv
    def context(store,task):
        if task['phase']==repair.PHASE:return new_context(store,task)
        result=original_context(store,task)
        result=features.attach_context(store,task,result)
        result['autonomy']=autonomy.context(store,task)
        result['git_boundary']={'version':ars.git_boundary.VERSION,'instruction':ars.git_boundary.INSTRUCTION}
        import execution_limits
        if execution_limits.unrestricted(store.state()):
            policy=dict(store.state()['config']['execution_limits'],instruction=execution_limits.INSTRUCTION)
            result['execution_limits']=policy
            result.setdefault('execution_workflow',{})['execution_limits']=policy
            result['execution_workflow']['job_runner']=str(HERE/'experiment_jobs.py')
        return result
    def reserve(store,task):
        ars.git_boundary.validate_state(store.state(),store.directory)
        operation=original_reserve(store,task)
        if operation:
            path=Path(operation['directory'])/'request.json'
            request=ars.read_json(path)
            if not request.get('model_assignment'):
                ars.atomic_json(path,routing.bind_request(request))
                with store.tx():store.event('operation.model_selected',{'operation_id':operation['id'],**request['model_assignment']})
            import usage_ledger
            usage_ledger.safe_sync(store)
        return operation
    def start(directory):
        store=ars.Store(directory)
        try:ars.git_boundary.validate_state(store.state(),store.directory)
        finally:store.close()
        return original_start(directory)
    def verify(result,store,task):
        accepted=result.get('status')=='done' and result.get('verdict')=='accept'
        checks=[dict(id='original',label='原固定执行端验收',criterion='原绑定验证器与原科学门槛')]
        if accepted:checks.append(dict(id='dashboard',label='本次观测契约检查',criterion='保留旧调用契约，新调用使用已登记要求'))
        tracking=verification_monitor.ControllerChecks(store,task,checks)
        verification=tracking.check('original','原固定执行端验收',lambda:new_verify(result,store,task) if task['phase']==repair.PHASE else original_verify(result,store,task))
        if accepted:
            verification['experiment_dashboard']=tracking.check('dashboard','本次观测契约检查',lambda:monitor.verify(store,task),skip_if_none=True)
        return verification
    def accept(store,task,operation_id,result,verification,recovery_mode='executor'):
        fn=new_accept if task['phase']==repair.PHASE else original_accept
        return fn(store,task,operation_id,result,verification,recovery_mode)
    def argv(request,schema_path,output_path):
        fn=new_argv if request['context'].get('code_repair') else original_argv
        arguments=routing.apply_argv(fn(request,schema_path,output_path),request)
        if '--skip-git-repo-check' not in arguments:
            arguments.append('--skip-git-repo-check')
        return arguments
    def advance(store):
        if store.state()['status'] in ('STOPPED_USER','STOPPED_BUDGET','COMPLETED','NEEDS_RECONCILIATION'):return
        with store.tx():
            if self_repair.maybe_queue(store):return
        if any(t['phase']==repair.PHASE and t['status'] in ('PENDING','RUNNING','UNKNOWN') for t in store.tasks()):return
        # Legacy dependency solvers must not mistake a repair operation for an
        # accepted research phase. The full ledger remains available elsewhere.
        tasks=store.tasks
        store.tasks=lambda:[t for t in tasks() if t['phase']!=repair.PHASE]
        try:original_advance(store)
        finally:store.tasks=tasks
        if store.state()['status']=='WAITING_EXTERNAL':
            with store.tx():autonomy.maybe_queue(store)
    ars.assemble_context=context;ars.verify_task_result=verify;ars.accept_task_result=accept
    ars.executor_argv=argv;ars.advance=advance
    ars.reserve_task=reserve;ars.start_campaign=start
    # Spawn every subsequent controller/activity through this same overlay.
    # HERE and verify_runtime_pin still refer to the original pinned executor.
    ars.__file__=str(HERE/'runtime_entry.py')
    return ars


def config_from_args():
    for flag in ('--campaign','--directory'):
        if flag in sys.argv:
            directory=Path(sys.argv[sys.argv.index(flag)+1])
            if flag=='--directory':return json.loads((directory/'request.json').read_text())['config']
            db=sqlite3.connect(f'file:{directory}/state.sqlite3?mode=ro',uri=True)
            try:return json.loads(db.execute('SELECT config FROM campaign').fetchone()[0])
            finally:db.close()
    raise ValueError('task runtime requires a campaign or operation directory')


if __name__=='__main__':
    cfg=config_from_args();pin=cfg.get('system_runtime_pin',{})
    if pin.get('enabled'):
        # Use the same recorded hash check as the campaign's own reservation.
        ars=install(check_pin(pin))
        if hasattr(ars,'verify_runtime_pin'):
            ars.verify_runtime_pin(cfg)
    else:
        import ars
    ars.main()
