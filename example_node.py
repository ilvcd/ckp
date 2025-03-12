import os
import sys
import torch
import numpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))



class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


any_type = AnyType("*")


def show_any(obj, max_len):
    if isinstance(obj, torch.Tensor):
        result = f'shape {tuple(obj.shape)}, min {obj.min()}, max {obj.max()}, median {torch.median(obj)}, content: {str(obj)}'
    elif isinstance(obj, numpy.ndarray):
        result = f'shape {tuple(obj.shape)}, min {obj.min()}, max {obj.max()}, median {numpy.median(obj)}, content: {str(obj)}'
    elif isinstance(obj, list) or isinstance(obj, tuple):
        result = 'list' if isinstance(obj, list) else 'tuple'
        result += f'({len(obj)})'
        if obj:
            result += f', obj[0]: {show_any(obj[0], max_len=max_len / len(obj))}'
    else:
        result = str(obj)
    if max_len > 0:
        result = result[:max_len]
    return result


def _print_to_console(header='', max_len=0, **kwargs):
    if header:
        print(f"{header}")


def _exec(expression, output_names, **kwargs):
    try:
        local_vars = dict()
        exec(expression, kwargs.copy(), local_vars)
        result = {
            name: local_vars.pop(name, None) for name in output_names
        }
        return result
    except Exception as ex:
        raise ex


def _evaluate(self, input_names, output_names, **kwargs):
    unique_id = int(kwargs.pop('unique_id'))
    workflow = kwargs.pop('extra_pnginfo')['workflow']
    nodes = workflow['nodes']
    found = False
    for one_node in nodes:
        if one_node['id'] == unique_id:
            assert not found
            found = True
            index = list(type(self).INPUT_TYPES()['required'].keys()).index('expression')
            expression = one_node['widgets_values'][index]
            kwargs['expression'] = expression
    assert found
    input = {
        name: kwargs.pop(name, None) for name in input_names
    }
    output = _exec(expression=expression, output_names=output_names, **input)
    if kwargs.pop('print_to_console') == "True":
        _print_to_console(header='Evaluate', expression=expression, **input, **output)
    return tuple((
        output[name] for name in output_names
    ))


class EvaluateMultiple1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "expression": ("STRING", {"default": "", "multiline": True}),
                "input_count": ("INT", {"default": 1, "min": 1, "max": 20, "step": 1}),
                "print_to_console": (["False", "True"],),
            },
            "optional": {
                f'in{idx}': (any_type, {}) for idx in range(1, 2)
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
    RETURN_TYPES = tuple([any_type] * 1)
    RETURN_NAMES = tuple([f'out{idx}' for idx in range(1, 2)])
    FUNCTION = "evaluate"
    CATEGORY = "utils"

    def evaluate(self, **kwargs):
        input_names = sorted(type(self).INPUT_TYPES()['optional'].keys())
        output_names = sorted(type(self).RETURN_NAMES)
        return _evaluate(self, input_names=input_names, output_names=output_names, **kwargs)

NODE_CLASS_MAPPINGS = {
    "Test Text": EvaluateMultiple1,
}
