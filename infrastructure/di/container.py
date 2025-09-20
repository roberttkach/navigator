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
from ...application.usecase.add import AddUseCase
from ...application.usecase.back import BackUseCase
from ...application.usecase.last import LastUseCase
from ...application.usecase.pop import PopUseCase
from ...application.usecase.rebase import RebaseUseCase
from ...application.usecase.replace import ReplaceUseCase
from ...application.usecase.set import SetUseCase
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
        chunk_size=chunk,
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
    rendering_config = providers.Object(RenderingConfig(detect_thumb_change=SETTINGS.detect_thumb_change))
    view_orchestrator = providers.Factory(
        ViewOrchestrator,
        gateway=gateway,
        inline=inline_strategy,
        rendering_config=rendering_config,
    )
    view_restorer = providers.Factory(
        ViewRestorer, markup_codec=markup_codec, factory_registry=registry
    )

    add_uc = providers.Factory(
        AddUseCase,
        history_repo=history_repo, state_repo=state_repo, last_repo=last_repo,
        orchestrator=view_orchestrator,
        mapper=entry_mapper, history_limit=history_limit,
    )
    replace_uc = providers.Factory(
        ReplaceUseCase,
        history_repo=history_repo, state_repo=state_repo, last_repo=last_repo,
        orchestrator=view_orchestrator,
        mapper=entry_mapper, history_limit=history_limit,
    )
    back_uc = providers.Factory(
        BackUseCase,
        history_repo=history_repo, state_repo=state_repo,
        gateway=gateway, restorer=view_restorer,
        orchestrator=view_orchestrator, last_repo=last_repo,
    )
    set_uc = providers.Factory(
        SetUseCase,
        history_repo=history_repo, state_repo=state_repo,
        gateway=gateway, restorer=view_restorer,
        orchestrator=view_orchestrator, last_repo=last_repo,
    )
    pop_uc = providers.Factory(PopUseCase, history_repo=history_repo, last_repo=last_repo)
    rebase_uc = providers.Factory(RebaseUseCase, history_repo=history_repo, temp_repo=temp_repo, last_repo=last_repo)
    last_uc = providers.Factory(
        LastUseCase, last_repo=last_repo, history_repo=history_repo, gateway=gateway,
        orchestrator=view_orchestrator,
    )
