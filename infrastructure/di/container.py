from dependency_injector import containers, providers

from ...adapters.aiogram.types import FSMContext
from ...adapters.storage.historyrepo import HistoryRepo
from ...adapters.storage.lastrepo import LastRepo
from ...adapters.storage.staterepo import StateRepo
from ...adapters.storage.temprepo import TempRepo
from ...adapters.storage.transitionrecorder import TransitionRecorder
from ...adapters.telegram.gateway import TelegramGateway
from ...adapters.telegram.markupcodec import AiogramMarkupCodec
from ...adapters.telegram.media import is_url_input_file
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
from ...domain.port.factory import ViewFactoryRegistry
from ...domain.service.rendering.config import RenderingConfig
from ...infrastructure.config import SETTINGS


class AppContainer(containers.DeclarativeContainer):
    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    registry = providers.Dependency(instance_of=ViewFactoryRegistry)

    history_limit = providers.Object(SETTINGS.history_limit)
    chunk = providers.Object(SETTINGS.chunk)

    markup_codec = providers.Singleton(AiogramMarkupCodec)
    gateway = providers.Singleton(
        TelegramGateway,
        bot=event.provided.bot,
        markup_codec=markup_codec,
        chunk=chunk,
        truncate=providers.Object(SETTINGS.truncate),
    )
    history_repo = providers.Factory(HistoryRepo, state=state)
    state_repo = providers.Factory(StateRepo, state=state)
    last_repo = providers.Factory(LastRepo, state=state)
    transition_observer = providers.Factory(TransitionRecorder, state_repo=state_repo)

    temp_repo = providers.Factory(TempRepo, state=state)
    entry_mapper = providers.Factory(EntryMapper, registry=registry)
    inline_strategy = providers.Factory(
        InlineStrategy,
        gateway=gateway,
        is_url_input_file=is_url_input_file,
        strict_inline_media_path=providers.Object(SETTINGS.strict_inline_media_path),
    )
    rendering_config = providers.Object(RenderingConfig(thumb_watch=SETTINGS.thumb_watch))
    view_orchestrator = providers.Factory(
        ViewOrchestrator,
        gateway=gateway,
        inline=inline_strategy,
        rendering_config=rendering_config,
    )
    view_restorer = providers.Factory(
        ViewRestorer, markup_codec=markup_codec, factory_registry=registry
    )

    appender = providers.Factory(
        Appender,
        history_repo=history_repo, state_repo=state_repo, last_repo=last_repo,
        orchestrator=view_orchestrator,
        mapper=entry_mapper, history_limit=history_limit,
    )
    swapper = providers.Factory(
        Swapper,
        history_repo=history_repo, state_repo=state_repo, last_repo=last_repo,
        orchestrator=view_orchestrator,
        mapper=entry_mapper, history_limit=history_limit,
    )
    rewinder = providers.Factory(
        Rewinder,
        history_repo=history_repo, state_repo=state_repo,
        gateway=gateway, restorer=view_restorer,
        orchestrator=view_orchestrator, last_repo=last_repo,
    )
    setter = providers.Factory(
        Setter,
        history_repo=history_repo, state_repo=state_repo,
        gateway=gateway, restorer=view_restorer,
        orchestrator=view_orchestrator, last_repo=last_repo,
    )
    trimmer = providers.Factory(Trimmer, history_repo=history_repo, last_repo=last_repo)
    shifter = providers.Factory(Shifter, history_repo=history_repo, temp_repo=temp_repo, last_repo=last_repo)
    tailer = providers.Factory(
        Tailer, last_repo=last_repo, history_repo=history_repo, gateway=gateway,
        orchestrator=view_orchestrator,
    )
    alarm = providers.Factory(
        Alarm,
        gateway=gateway,
    )
