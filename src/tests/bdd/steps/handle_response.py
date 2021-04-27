from behave import then
import json
from deepdiff import DeepDiff
import pprint

from utils.data_structure.compare import pretty_eq
from utils.data_structure.find import find

STATUS_CODES = {
    "OK": 200,
    "Created": 201,
    "No Content": 204,
    "Bad Request": 400,
    "Unprocessable Entity": 422,
    "Unauthorized": 401,
    "Not Found": 404,
    "Conflict": 409,
    "System Error": 500,
}


@then('the response status should be "{status}"')
def step_response_status(context, status):
    if context.response.status_code != STATUS_CODES[status]:
        pp = pprint.PrettyPrinter(indent=2)
        pretty_print = "\n Actual: \n {} \n Expected: \n {}".format(
            pp.pformat(context.response.status_code), pp.pformat(STATUS_CODES[status])
        )
        print(pretty_print)
        print(context.response.json())
    assert context.response.status_code == STATUS_CODES[status]


@then("the response should equal")
def step_impl_equal(context):
    actual = context.response.json()
    data = context.text or context.data
    expected = json.loads(data)
    result = DeepDiff(expected, actual, ignore_order=True)
    if result != {}:
        print(result)
        print(actual)
    assert result == {}


@then("the response at {dot_path} should equal")
def step_impl_equal_dot_path(context, dot_path):
    actual = context.response.json()
    target = find(actual, dot_path.split("."))
    data = context.text or context.data
    expected = json.loads(data)
    result = DeepDiff(target, expected, ignore_order=True)
    if result != {}:
        print("Actual:", target)
        print("Expected:", expected)
    assert result == {}


@then("the response should contain")
def step_impl_contain(context):
    actual = context.response.json()
    data = context.text or context.data
    expected = json.loads(data)
    pretty_eq(expected, actual)


@then("the array at {dot_path} should be of length {length}")
def step_impl_array_length(context, dot_path, length):
    actual = context.response.json()
    target = find(actual, dot_path.split("."))
    result = len(target) == int(length)
    if not result:
        print(f"array is of length {len(target)}")
        print("array:", target)
    assert result


@then("the response should be")
def step_impl_should_be(context):
    actual = context.response.json()
    data = context.text or context.data
    pretty_eq(data, actual)


@then("the length of the response should not be zero")
def step_impl(context):
    assert int(context.response.headers["content-length"]) != 0