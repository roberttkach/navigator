# Архитектурные изменения

## Разделение телеметрии и бизнес-логики

1. **`Shifter` использует выделенную `RebaseInstrumentation`**
   - **Местоположение:** `app/usecase/rebase.py`, `app/usecase/rebase_instrumentation.py`
   - **Изменение:** Телеметрия вынесена в отдельный инструмент, который оборачивает трассировку и события. Сам класс `Shifter` теперь отвечает только за пересборку истории и обновление маркера.
   - **Фрагмент:**
     ```python
     await self._instrumentation.traced(marker, self._perform)
     self._instrumentation.history_saved(len(rebuilt))
     ```

2. **Телеметрия оторвана от `RetreatWorkflow`**
   - **Местоположение:** `presentation/telegram/back.py`
   - **Изменение:** Телеметрия UI обрабатывается в `RetreatHandler`, а `RetreatWorkflow` фокусируется на построении контекста и доменной логике.
   - **Фрагмент:**
     ```python
     result = await self._workflow.execute(cb, navigator, payload)
     if result.success:
         self._telemetry.completed(scope)
     ```

## Снижение связанности между слоями

1. **`NavigatorDependencies` перенесён из слоя представления в сервисный слой**
   - **Местоположение:** `app/service/navigator_runtime/dependencies.py`
   - **Изменение:** DI-контейнер инфраструктуры и утилиты загрузки теперь импортируют зависимости из общего сервисного модуля, исключая прямую привязку к представлению.
   - **Фрагмент:**
     ```python
     from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
     ```

## Повышение связности модулей

1. **Политики разбиты по назначению**
   - **Местоположение:** `app/internal/policy/prime.py`, `app/internal/policy/shield.py`
   - **Изменение:** Подготовка сообщений (`prime`) и inline-валидация (`shield`) вынесены в отдельные файлы и объединены через пакет, что упрощает навигацию и повторное использование.
   - **Фрагмент:**
     ```python
     from navigator.app.internal.policy import prime, shield
     ```

## Выделение слоя телеметрии

1. **`RewindHistoryWriter` получает телеметрию через `RewindWriteTelemetry`**
   - **Местоположение:** `app/usecase/back_access.py`
   - **Изменение:** Класс записи истории больше не управляет каналом напрямую и концентрируется на взаимодействии с репозиториями.
   - **Фрагмент:**
     ```python
     await self._latest.mark(identifier)
     self._instrumentation.latest_marked(identifier)
     ```
