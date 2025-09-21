from enum import Enum


class LogCode(Enum):
    # Render / Rerender
    RENDER_START = "render_start"
    RENDER_OK = "render_ok"
    RENDER_SKIP = "render_skip"
    RERENDER_START = "rerender_start"
    RERENDER_INLINE_NO_FALLBACK = "rerender_inline_no_fallback"

    # Inline
    INLINE_DROP_EXTRA = "inline_drop_extra"
    INLINE_CONTENT_SWITCH_FORBIDDEN = "inline_content_switch_forbidden"
    INLINE_DELETE_SEND_FORBIDDEN = "inline_delete_send_forbidden"
    INLINE_TAIL_DELETE_IDS = "inline_tail_delete_ids"
    INLINE_REMAP_DELETE_SEND = "inline_remap_delete_send"

    # Albums
    ALBUM_PARTIAL_OK = "album_partial_ok"
    ALBUM_PARTIAL_FALLBACK = "album_partial_fallback"

    # History / Last / State / Graph / Temp
    HISTORY_LOAD = "history_load"
    HISTORY_SAVE = "history_save"
    HISTORY_TRIM = "history_trim"
    LAST_GET = "last_get"
    LAST_SET = "last_set"
    LAST_DELETE = "last_delete"
    STATE_GET = "state_get"
    STATE_SET = "state_set"
    STATE_DATA_GET = "state_data_get"
    GRAPH_GET = "graph_get"
    GRAPH_SAVE = "graph_save"
    TEMP_LOAD = "temp_load"
    TEMP_SAVE = "temp_save"

    # Registry / Navigator / Router
    REGISTRY_REGISTER = "registry_register"
    REGISTRY_GET = "registry_get"
    REGISTRY_HAS = "registry_has"
    NAVIGATOR_API = "navigator_api"
    ROUTER_BACK_ENTER = "router_back_enter"
    ROUTER_BACK_DONE = "router_back_done"
    ROUTER_BACK_FAIL = "router_back_fail"

    # Gateway
    GATEWAY_SEND_OK = "gateway_send_ok"
    GATEWAY_SEND_FAIL = "gateway_send_fail"
    GATEWAY_EDIT_OK = "gateway_edit_ok"
    GATEWAY_EDIT_FAIL = "gateway_edit_fail"
    GATEWAY_DELETE_OK = "gateway_delete_ok"
    GATEWAY_DELETE_FAIL = "gateway_delete_fail"
    GATEWAY_NOTIFY_EMPTY = "gateway_notify_empty"
    TELEGRAM_RETRY = "telegram_retry"

    # Extras / Serializer
    EXTRA_FILTERED_OUT = "extra_filtered_out"
    EXTRA_UNKNOWN_DROPPED = "extra_unknown_dropped"
    EXTRA_EFFECT_STRIPPED = "extra_effect_stripped"
    MARKUP_ENCODE = "markup_encode"
    MARKUP_DECODE = "markup_decode"

    # Media / Limits
    MEDIA_UNSUPPORTED = "media_unsupported"
    TOO_LONG_TRUNCATED = "too_long_truncated"

    # Transitions / Ops
    TRANSITION = "transition"
    POP_SUCCESS = "pop_success"
    REBASE_SUCCESS = "rebase_success"
    RESTORE_DYNAMIC = "restore_dynamic"
    RESTORE_DYNAMIC_FALLBACK = "restore_dynamic_fallback"
