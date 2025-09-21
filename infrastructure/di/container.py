from dependency_injector import containers, providers

from ...adapters.aiogram.types import FSMContext
from ...adapters.storage.historyrepo import HistoryRepo
from ...adapters.storage.lastrepo import LastRepo
from ...adapters.storage.staterepo import StateRepo
from ...adapters.storage.temprepo import TempRepo
from ...adapters.storage.transitionrecorder import TransitionRecorder
from ...adapters.telegram.gateway import TelegramGateway
from ...adapters.telegram.markupcodec import AiogramMarkupCodec
from ...adapters.telegram.media import weblink
from ...application.map.entry import EntryMapper
from ...application.service.view.inline import InlineStrategy
from ...application.service.view.orchestrator import ViewOrchestrator
from ...application.service.view.restorer import ViewRestorer
from ...application.usecase.add import Appender
from ...application.usecase.back import Rewinder
from ...application.usecase.last import Tailer
from ...application.usecase.alarm import Alarm
from ...application.usecase.pop import Trimmer
from ...application.usecase.rebase import Shifter
from ...application.usecase.replace import Swapper
from ...application.usecase.set import Setter
from ...domain.port.factory import ViewLedger
from ...domain.service.rendering.config import RenderingConfig
from ...infrastructure.config import SETTINGS


class AppContainer(containers.DeclarativeContainer):
    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    ledger = providers.Dependency(instance_of=ViewLedger)

    retention = providers.Object(SETTINGS.retention)
    chunk = providers.Object(SETTINGS.chunk)

    codec = providers.Singleton(AiogramMarkupCodec)
    gateway = providers.Singleton(
        TelegramGateway,
        bot=event.provided.bot,
        codec=codec,
        chunk=chunk,
        truncate=providers.Object(SETTINGS.truncate),
    )
    chronicle = providers.Factory(HistoryRepo, state=state)
    status = providers.Factory(StateRepo, state=state)
    latest = providers.Factory(LastRepo, state=state)
    observer = providers.Factory(TransitionRecorder, status=status)

    buffer = providers.Factory(TempRepo, state=state)
    mapper = providers.Factory(EntryMapper, ledger=ledger)
    strategy = providers.Factory(
        InlineStrategy,
        gateway=gateway,
        probe=weblink,
        strictpath=providers.Object(SETTINGS.strictpath),
    )
    rendering = providers.Object(RenderingConfig(thumbguard=SETTINGS.thumbguard))
    orchestrator = providers.Factory(
        ViewOrchestrator,
        gateway=gateway,
        inline=strategy,
        rendering_config=rendering,
    )
    restorer = providers.Factory(
        ViewRestorer, codec=codec, ledger=ledger
    )

    appender = providers.Factory(
        Appender,
        archive=chronicle, state=status, tail=latest,
        orchestrator=orchestrator,
        mapper=mapper, limit=retention,
    )
    swapper = providers.Factory(
        Swapper,
        archive=chronicle, state=status, tail=latest,
        orchestrator=orchestrator,
        mapper=mapper, limit=retention,
    )
    rewinder = providers.Factory(
        Rewinder,
        ledger=chronicle, status=status,
        gateway=gateway, restorer=restorer,
        orchestrator=orchestrator, latest=latest,
    )
    setter = providers.Factory(
        Setter,
        ledger=chronicle, status=status,
        gateway=gateway, restorer=restorer,
        orchestrator=orchestrator, latest=latest,
    )
    trimmer = providers.Factory(Trimmer, ledger=chronicle, latest=latest)
    shifter = providers.Factory(Shifter, ledger=chronicle, buffer=buffer, latest=latest)
    tailer = providers.Factory(
        Tailer, latest=latest, ledger=chronicle, gateway=gateway,
        orchestrator=orchestrator,
    )
    alarm = providers.Factory(
        Alarm,
        gateway=gateway,
    )
