from .models import ModelBase
from .api_models import APIModels


def model_factory(
        model_type: str,
        name: str,
        model_path: str,
        **args
) -> ModelBase:
    if model_type == 'api':
        model = APIModels(name, model_path, **args)
    if model_type == 'local':
        # from .qwen_local import QwenLocal
        # return QwenLocal(**kwargs)
        model = APIModels(name, model_path, **args)
    else:
        raise NotImplementedError

    print(f'{model_type}: {model_path} loaded.', flush=True)
    return model
