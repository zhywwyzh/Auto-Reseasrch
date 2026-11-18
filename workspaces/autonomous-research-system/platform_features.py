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
