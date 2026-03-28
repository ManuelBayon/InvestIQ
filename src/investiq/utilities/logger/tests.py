from engine.utilities.logger.access import _get_base_logger, get_contextual_logger, _get_child_logger
from engine.utilities.logger.factory import LoggerFactory
from engine.utilities.logger.setup import init_base_logger

init_base_logger(debug=True)

def test_root_logger() -> None:
    logger = _get_base_logger()
    assert logger.name == "InvestIQ"

def test_logger_single_child() -> None:
    logger = _get_child_logger("child")
    assert logger.name == "InvestIQ.child"

def test_contextual_logger() -> None:
    logging_adapter = get_contextual_logger(
        child_name="child",
        engine_type="engine_type",
        run_id="123",
        strategy="mean-revert",
        account="demo"
    )
    assert logging_adapter.name == "InvestIQ.child"
    assert logging_adapter.extra["engine_type"] == "engine_type"
    assert logging_adapter.extra["run_id"] == "123"
    assert logging_adapter.extra["strategy"] == "mean-revert"
    assert logging_adapter.extra["account"] == "demo"

def test_logger_factory() -> None:
    factory = LoggerFactory(
        engine_type="test_engine",
        run_id="123"
    )
    new_factory: LoggerFactory = factory.child("1").child("2")
    logger = new_factory.get()
    assert logger.name == "InvestIQ.1.2"

    factory_2 = new_factory.child("3")
    logger_2 = factory_2.get()
    assert logger_2.name == "InvestIQ.1.2.3"






