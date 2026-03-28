from ib_insync import Contract

from investiq.market_data.domain.requests.base import RequestSpec
from investiq.market_data.domain.instruments.base import ProviderInstrumentSpec
from investiq.market_data.adapters.ibkr.contracts import to_ibkr_contract


def build_ibkr_request(
    instrument: ProviderInstrumentSpec,
    request: RequestSpec,
) -> dict:

    contract: Contract = to_ibkr_contract(instrument)

    return {
        "contract": contract,
        "endDateTime": "",
        "durationStr": request.duration,
        "barSizeSetting": request.bar_size.value,
        "whatToShow": request.what_to_show.value,
        "useRTH": False,
    }