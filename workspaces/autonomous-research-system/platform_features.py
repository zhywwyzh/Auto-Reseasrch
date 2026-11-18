"""Default engineering capabilities for every registered research run.

Capability availability grants no experimental, scientific or resource authority.
Old configurations inherit these defaults without rewriting research evidence.
"""
VERSION = 'platform-observability-v1'
from pathlib import Path


def describe():
    return {'version': VERSION, 'scope': 'all_registered_runs',
            'task_instructions': True, 'executor_identity': True,
            'lifecycle_dates': True, 'scoped_supplements': True,
            'request_model_tokens': True, 'experiment_dashboard': True, 'stage_model_routing': True,
            'adaptive_execution_visibility': True, 'job_logs_and_state_explanations': True,
            'live_verification_tracking': True,
            'defaults_apply_to_existing_and_future_runs': True,
            'scientific_authority_changed': False}


def attach_context(store, task, context):
    import experiment_monitor
    import task_trace
    import manuscript_quality
    import execution_visibility
    import verification_monitor
    context['platform_features'] = describe()
    import code_repair
    if code_repair.enabled(store.state()):
        context['repair_handoff'] = {
            'instruction': '如果已定位系统源码缺陷且目标超出本任务写入范围，在本运行artifacts下保存'
                'controller-handoff.json，在本次blocked结果的local_file证据中引用其原文。'
                '控制器核对来源和版本后接管，保留原始错误及下次复验依据。',
            'fields': {'blocker_kind': 'controller_write_scope_required',
                       'target': '目标系统Python模块的仓库相对路径',
                       'expected_current_source_sha256': '已核对的目标源码SHA256'}}
        repair = context.get('self_repair')
        if repair and repair.get('diagnosis_only') and code_repair.repaired_since_diagnosis(store, task):
            repair.update(diagnosis_only=False, instruction='控制器已修复并复验候选代码。'
                '读取code_repair.verified及其证据，在本任务原授权范围内复验同版结果，'
                '保留旧失败并接续原阶段。先核对已有作业回执，禁止盲目重投。')
    context['manuscript_writing'] = manuscript_quality.INSTRUCTION
    context['execution_visibility'] = execution_visibility.context(store)
    context['verification_tracking'] = verification_monitor.context(store,task)
    context['user_supplements'] = task_trace.context(store, task)
    context['supplement_policy'] = ('逐条核对补充的适用范围与正文要求；按指定阶段执行，不提前越过科学验收，'
                                    '不扩大预算或授权。在结果中引用适用补充id并说明处理情况。')
    dashboard = experiment_monitor.prepare(store.state(), store.directory, task)
    if dashboard:
        workflow = context.setdefault('execution_workflow', {})
        workflow['experiment_dashboard'] = dashboard
        workflow['job_runner'] = str(Path(experiment_monitor.__file__).with_name('experiment_jobs.py'))
    return context
