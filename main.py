from pathlib import Path

import pygame
import sys
import random
import math
import json
import os
from typing import List, Dict, Optional, Tuple, Union, Set, Any

# Размеры окна
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WIDTH, HEIGHT = 800, 600
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# Цвета
BLUE_DARK = (5, 5, 30)
BLUE_LIGHT = (10, 10, 50)
WHITE = (223, 223, 223)  # Не чисто белый для ретро-эффекта
YELLOW = (255, 255, 0)
RED = (200, 50, 50)
RED_HOVER = (230, 80, 80)
GREEN = (0, 200, 0)
GREEN_HOVER = (0, 230, 0)
BLUE_BUTTON = (50, 50, 150)
BLUE_BUTTON_HOVER = (70, 70, 200)

# Цвета интерфейса
UI_PANEL_BG = (30, 30, 60)
UI_BORDER = WHITE
UI_DIALOG_BG = (20, 20, 50, 220)  # Полупрозрачный фон диалогов
UI_CHOICE_BG = (30, 30, 70, 240)  # Полупрозрачный фон выбора
UI_BUTTON_COLOR = BLUE_BUTTON
UI_BUTTON_HOVER = BLUE_BUTTON_HOVER

# Настройки шрифтов
FONT_LARGE = pygame.font.SysFont("Courier New", 36, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Courier New", 24, bold=True)
FONT_SMALL = pygame.font.SysFont("Courier New", 16, bold=True)

# Настройки игры
GAME_TITLE = "Ради страны"
MAX_ZOOM = 20.0
ZOOM_SPEED = 0.1
STAR_COUNT = 200
PARTICLE_COUNT = 20

# Пути к файлам
MUSIC_FOLDER = "music"
SAVE_FILE = "game_save.json"
SETTINGS_FILE = "game_settings.json"
STORY_FILE = "story.json"
IMAGE_PATTERN = "pics/image{}.jpg"

# Состояния игры
class GameState:
    MENU = 0
    ZOOM = 1
    PLAY = 2
    ENDING = 3

# Размеры элементов UI
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
PANEL_WIDTH = 200
PANEL_HEIGHT = 400
DIALOG_WIDTH = SCREEN_WIDTH - 100
DIALOG_HEIGHT = 140
DIALOG_MARGIN = 50

# Настройки эффектов
SHAKE_INTENSITY = 3
SHAKE_DURATION = 10
PARTICLE_LIFETIME = 30  # кадров


class Locale:
    def __init__(self, file_path: str = 'locales.json'):
        self.translations: Dict[str, Any] = {}
        self.default_lang = "ru"
        self.load_translations(Path(__file__).parent / file_path)

    def load_translations(self, file_path: Path) -> None:
        """Загружает переводы из JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading translations: {e}")
            self.translations = {}

    def get(self, key: str, lang: str = None) -> str:
        """
        Получает перевод по ключу для указанного языка
        :param key: Ключ перевода в формате 'category.subkey'
        :param lang: Язык перевода (если None, используется язык по умолчанию)
        :return: Найденный перевод или ключ в квадратных скобках, если не найден
        """
        if not self.translations:
            return f"[{key}]"

        lang = lang or self.default_lang
        if lang not in self.translations:
            lang = self.default_lang

        keys = key.split('.')
        result = self.translations[lang]

        for k in keys:
            if not isinstance(result, dict):
                break
            result = result.get(k, {})

        if not result or isinstance(result, dict):
            return f"[{key}]"

        return result

    def set_default_language(self, lang: str) -> None:
        """Устанавливает язык по умолчанию"""
        if lang in self.translations:
            self.default_lang = lang

class MusicPlayer:
    def __init__(self, music_folder="music", volume=0.5):
        self.music_folder = Path(__file__).parent / music_folder
        self.playlist = []
        self.current_track_index = 0
        self.volume = volume
        self._original_playlist = []  # Для сохранения оригинального порядка

        # Инициализация микшера pygame с оптимальными параметрами
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

        self.load_playlist()

    def load_playlist(self):
        """Загружает все поддерживаемые аудиофайлы из указанной папки"""
        supported_formats = ('.mp3', '.ogg', '.wav')
        self.playlist = []

        try:
            if not self.music_folder.exists():
                self.music_folder.mkdir(parents=True)
                print(f"Папка {self.music_folder} создана. Добавьте в нее музыку.")
                return

            for file in self.music_folder.glob('*'):
                if file.suffix.lower() in supported_formats:
                    self.playlist.append(file)

            self._original_playlist = self.playlist.copy()

            if not self.playlist:
                print(f"В папке {self.music_folder} не найдено поддерживаемых аудиофайлов.")
            else:
                print(f"Загружено {len(self.playlist)} треков в плейлист.")

        except Exception as e:
            print(f"Ошибка загрузки плейлиста: {e}")

    def play(self, shuffle=False):
        """Начинает воспроизведение плейлиста"""
        if not self.playlist:
            print("Нет треков для воспроизведения.")
            return

        if shuffle:
            current_track = self.playlist[self.current_track_index] if self.playlist else None
            random.shuffle(self.playlist)
            if current_track:
                self.current_track_index = self.playlist.index(current_track)
        elif self._original_playlist and len(self.playlist) == len(self._original_playlist):
            # Восстанавливаем оригинальный порядок, если нужно
            current_track = self.playlist[self.current_track_index]
            self.playlist = self._original_playlist.copy()
            self.current_track_index = self.playlist.index(current_track)

        self._play_current_track()

    def _play_current_track(self):
        """Воспроизводит текущий трек"""
        if not self.playlist:
            return

        try:
            pygame.mixer.music.load(str(self.playlist[self.current_track_index]))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            print(f"Сейчас играет: {self.playlist[self.current_track_index].stem}")
        except pygame.error as e:
            print(f"Ошибка воспроизведения: {e}")

    def next_track(self):
        """Переключает на следующий трек"""
        if not self.playlist:
            return

        self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
        self._play_current_track()

    def prev_track(self):
        """Переключает на предыдущий трек"""
        if not self.playlist:
            return

        self.current_track_index = (self.current_track_index - 1) % len(self.playlist)
        self._play_current_track()

    def set_volume(self, volume):
        """Устанавливает громкость (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)

    def stop(self):
        """Останавливает воспроизведение"""
        pygame.mixer.music.stop()

    def pause(self):
        """Приостанавливает воспроизведение"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()

    def unpause(self):
        """Возобновляет воспроизведение"""
        pygame.mixer.music.unpause()

    def update(self, events):
        """Обрабатывает события окончания трека"""
        for event in events:
            if event.type == pygame.USEREVENT and event.type == pygame.mixer.music.get_endevent():
                self.next_track()

class SettingsConfig:
    """Класс для хранения текущих значений настроек с поддержкой локализации"""

    def __init__(self):
        self._settings: Dict[str, Any] = {
            "music_volume": 0.5,
            "sound_volume": 0.7,
            "fullscreen": False,
            "language": "ru",
            "resolution": "800x600",
            "text_speed": 1.0
        }
        self._localized_settings: Dict[str, Dict[str, str]] = {}
        self._load_localization()

    def _load_localization(self) -> None:
        """Загружает локализованные названия настроек"""
        try:
            with open(Path(__file__).parent / 'locales.json', 'r', encoding='utf-8') as f:
                translations = json.load(f)
                lang = self._settings["language"]
                self._localized_settings = translations.get(lang, {}).get("settings", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self._localized_settings = {}

    def get(self, key: str, default=None) -> Any:
        """Получить значение настройки"""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Установить значение настройки"""
        if key in self._settings:
            self._settings[key] = value
            if key == "language":
                self._load_localization()  # Перезагружаем локализацию при смене языка

class SettingsManager:
    """Класс для работы с настройками игры с поддержкой локализации"""

    def __init__(self, config: SettingsConfig):
        self.config = config
        self.settings_file = Path("game_settings.json")
        self._localized_messages = self._load_localized_messages()

    def _load_localized_messages(self) -> Dict[str, str]:
        """Загружает локализованные сообщения для менеджера настроек"""
        try:
            with open(Path(__file__).parent / 'locales.json', 'r', encoding='utf-8') as f:
                translations = json.load(f)
                lang = self.config.get("language", "ru")
                return translations.get(lang, {}).get("settings_manager", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_localized_message(self, key: str, default: str = "") -> str:
        """Возвращает локализованное сообщение"""
        return self._localized_messages.get(key, default)

    def load_settings(self) -> bool:
        """Загрузить настройки из файла"""
        try:
            if not self.settings_file.exists():
                print(self.get_localized_message("file_not_found", "Файл настроек не найден"))
                return False

            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                for key, value in loaded.items():
                    self.config.set(key, value)

            print(self.get_localized_message("load_success", "Настройки успешно загружены"))
            return True

        except json.JSONDecodeError:
            print(self.get_localized_message("load_error_json", "Ошибка чтения файла настроек (неверный формат)"))
            return False
        except IOError:
            print(self.get_localized_message("load_error_io", "Ошибка чтения файла настроек"))
            return False

    def save_settings(self) -> bool:
        """Сохранить текущие настройки в файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.get_all(), f, indent=2, ensure_ascii=False)

            print(self.get_localized_message("save_success", "Настройки успешно сохранены"))
            return True
        except IOError:
            print(self.get_localized_message("save_error", "Ошибка сохранения настроек"))
            return False

    def reset_to_default(self) -> None:
        """Сбросить настройки к значениям по умолчанию"""
        self.config._settings = SettingsConfig()._settings
        print(self.get_localized_message("reset_success", "Настройки сброшены к значениям по умолчанию"))

class SettingsUI:
    """Полноценный класс для отрисовки и взаимодействия с интерфейсом настроек"""

    def __init__(self, config, manager, language: str = "ru"):
        """
        Инициализация UI настроек
        :param config: экземпляр SettingsConfig
        :param manager: экземпляр SettingsManager
        :param language: текущий язык интерфейса
        """
        self.config = config
        self.manager = manager
        self.language = language

        # Основные параметры окна
        self.window_width = 500
        self.window_height = 600
        self.padding = 20
        self.button_height = 40

        # Состояния элементов
        self.hovered_item = None
        self.scroll_offset = 0
        self.music_track_scroll = 0

        # Инициализация элементов управления
        self._init_ui_elements()

    def _init_ui_elements(self):
        """Создание всех UI элементов"""
        # Основное окно
        self.window_rect = pygame.Rect(
            (SCREEN_WIDTH - self.window_width) // 2,
            (SCREEN_HEIGHT - self.window_height) // 2,
            self.window_width,
            self.window_height
        )

        # Кнопка закрытия
        self.close_btn = pygame.Rect(
            self.window_rect.right - 40,
            self.window_rect.y + 15,
            30,
            30
        )

        # Элементы управления звуком
        self.volume_slider = {
            'rect': pygame.Rect(0, 0, 300, 20),
            'handle_rect': pygame.Rect(0, 0, 15, 30),
            'dragging': False
        }

        # Кнопки плеера
        btn_size = 40
        spacing = 15
        player_x = self.window_rect.x + (self.window_width - (4 * btn_size + 3 * spacing)) // 2

        self.player_buttons = {
            'shuffle': pygame.Rect(player_x, 0, btn_size, btn_size),
            'prev': pygame.Rect(player_x + btn_size + spacing, 0, btn_size, btn_size),
            'play': pygame.Rect(player_x + 2 * (btn_size + spacing), 0, btn_size, btn_size),
            'next': pygame.Rect(player_x + 3 * (btn_size + spacing), 0, btn_size, btn_size)
        }

        # Кнопки переключения режимов
        self.toggle_buttons = {
            'fullscreen': {
                'rect': pygame.Rect(0, 0, 100, self.button_height),
                'state': self.config.get('fullscreen')
            },
            'language': {
                'rect': pygame.Rect(0, 0, 100, self.button_height),
                'state': self.config.get('language')
            }
        }

        # Кнопка сохранения
        self.save_btn = pygame.Rect(0, 0, 150, self.button_height)

    def _update_positions(self):
        """Обновление позиций элементов при изменении размера окна"""
        btn_size = 40
        y_offset = self.window_rect.y + 60

        # Громкость звука
        self.volume_slider['rect'].update(
            self.window_rect.x + 50,
            y_offset + 10,
            300,
            20
        )
        self._update_volume_handle()
        y_offset += 50

        # Элементы плеера
        for btn in self.player_buttons.values():
            btn.y = y_offset
        y_offset += btn_size + 30

        # Полноэкранный режим
        self.toggle_buttons['fullscreen']['rect'].update(
            self.window_rect.x + self.window_width - 150,
            y_offset,
            100,
            self.button_height
        )
        y_offset += 50

        # Язык
        self.toggle_buttons['language']['rect'].update(
            self.window_rect.x + self.window_width - 150,
            y_offset,
            100,
            self.button_height
        )
        y_offset += 80

        # Кнопка сохранения
        self.save_btn.update(
            self.window_rect.centerx - 75,
            self.window_rect.bottom - 70,
            150,
            self.button_height
        )

    def _update_volume_handle(self):
        """Обновление позиции ползунка громкости"""
        volume = self.config.get('music_volume', 0.5)
        slider = self.volume_slider['rect']
        handle = self.volume_slider['handle_rect']

        handle_x = slider.x + (slider.width - handle.width) * volume
        handle.centerx = max(slider.left, min(slider.right, handle_x))
        handle.centery = slider.centery

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка всего интерфейса настроек"""
        self._update_positions()

        # Фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Основное окно
        pygame.draw.rect(surface, UI_PANEL_BG, self.window_rect, border_radius=15)
        pygame.draw.rect(surface, UI_BORDER, self.window_rect, 2, border_radius=15)

        # Заголовок
        title = FONT_LARGE.render(self.locale.get('ui.settings_title'), True, WHITE)
        surface.blit(title, (self.window_rect.centerx - title.get_width() // 2, self.window_rect.y + 20))

        # Кнопка закрытия
        self._draw_close_button(surface)

        # Отрисовка разделов
        self._draw_volume_control(surface)
        self._draw_music_player(surface)
        self._draw_toggle_buttons(surface)
        self._draw_save_button(surface)

    def _draw_close_button(self, surface: pygame.Surface) -> None:
        """Отрисовка кнопки закрытия"""
        is_hovered = self.close_btn.collidepoint(pygame.mouse.get_pos())
        color = RED_HOVER if is_hovered else RED

        pygame.draw.rect(surface, color, self.close_btn, border_radius=15)
        pygame.draw.rect(surface, WHITE, self.close_btn, 1, border_radius=15)

        # Текст "X"
        text = FONT_MEDIUM.render("×", True, WHITE)
        surface.blit(text, (self.close_btn.centerx - text.get_width() // 2,
                            self.close_btn.centery - text.get_height() // 2))

    def _draw_volume_control(self, surface: pygame.Surface) -> None:
        """Отрисовка управления громкостью"""
        y_pos = self.window_rect.y + 80

        # Заголовок
        title = FONT_SMALL.render(
            f"{self.locale.get('settings.volume')}: {int(self.config.get('music_volume', 0.5) * 100)}%",
            True,
            WHITE
        )

        # Ползунок
        slider = self.volume_slider['rect']
        pygame.draw.rect(surface, (50, 50, 80), slider, border_radius=10)
        pygame.draw.rect(surface, WHITE, slider, 1, border_radius=10)

        # Бегунок
        handle = self.volume_slider['handle_rect']
        pygame.draw.rect(surface, BLUE_BUTTON_HOVER, handle, border_radius=5)
        pygame.draw.rect(surface, WHITE, handle, 1, border_radius=5)

    def _draw_music_player(self, surface: pygame.Surface) -> None:
        """Отрисовка элементов управления музыкой"""
        y_pos = self.window_rect.y + 150

        # Кнопки управления
        for btn_type, btn_rect in self.player_buttons.items():
            is_hovered = btn_rect.collidepoint(pygame.mouse.get_pos())
            color = BLUE_BUTTON_HOVER if is_hovered else BLUE_BUTTON

            pygame.draw.rect(surface, color, btn_rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, btn_rect, 1, border_radius=5)

            # Иконки кнопок
            self._draw_player_icon(surface, btn_type, btn_rect)

        # Название трека (с эффектом бегущей строки)
        self._draw_track_name(surface, y_pos + 50)

    def _draw_toggle_buttons(self, surface: pygame.Surface) -> None:
        """Отрисовка переключателей (полноэкранный режим, язык)"""
        for key, data in self.toggle_buttons.items():
            is_hovered = data['rect'].collidepoint(pygame.mouse.get_pos())
            color = BLUE_BUTTON_HOVER if is_hovered else BLUE_BUTTON

            # Рисуем кнопку
            pygame.draw.rect(surface, color, data['rect'], border_radius=5)
            pygame.draw.rect(surface, WHITE, data['rect'], 1, border_radius=5)

            # Текст и состояние
            text_key = f"settings.{key}"
            text = FONT_SMALL.render(
                f"{self.locale.get(text_key, key)}: {'ON' if data['state'] else 'OFF'}",
                True,
                WHITE
            )
            surface.blit(
                text,
                (
                    data['rect'].centerx - text.get_width() // 2,
                    data['rect'].centery - text.get_height() // 2
                )
            )

    def _draw_player_icon(self, surface: pygame.Surface, btn_type: str, rect: pygame.Rect) -> None:
        """Отрисовка иконок для кнопок плеера"""
        icon_color = WHITE
        margin = 10
        line_width = 3  # Толщина линий для векторных иконок

        if btn_type == 'shuffle':
            # Иконка перемешивания (две стрелки)
            # Левая стрелка
            pygame.draw.line(surface, icon_color,
                             (rect.x + margin + 5, rect.centery + 5),
                             (rect.x + margin, rect.centery), line_width)
            pygame.draw.line(surface, icon_color,
                             (rect.x + margin, rect.centery),
                             (rect.x + margin + 5, rect.centery - 5), line_width)

            # Правая стрелка
            pygame.draw.line(surface, icon_color,
                             (rect.right - margin - 5, rect.centery - 5),
                             (rect.right - margin, rect.centery), line_width)
            pygame.draw.line(surface, icon_color,
                             (rect.right - margin, rect.centery),
                             (rect.right - margin - 5, rect.centery + 5), line_width)

            # Волнообразная линия между стрелками
            wave_points = [
                (rect.x + margin + 10, rect.centery + 3),
                (rect.centerx - 10, rect.centery - 2),
                (rect.centerx, rect.centery + 4),
                (rect.centerx + 10, rect.centery - 3)
            ]
            pygame.draw.lines(surface, icon_color, False, wave_points, line_width)

        elif btn_type == 'prev':
            # Двойная стрелка влево
            # Первый треуголник
            pygame.draw.polygon(surface, icon_color, [
                (rect.x + margin, rect.centery),
                (rect.x + margin + 15, rect.y + margin),
                (rect.x + margin + 15, rect.bottom - margin)
            ])

            # Второй треугольник (с отступом)
            pygame.draw.polygon(surface, icon_color, [
                (rect.x + margin + 20, rect.centery),
                (rect.x + margin + 35, rect.y + margin),
                (rect.x + margin + 35, rect.bottom - margin)
            ])

        elif btn_type == 'play':
            if pygame.mixer.music.get_busy():  # Пауза
                # Две вертикальные линии
                pygame.draw.rect(surface, icon_color,
                                 (rect.x + margin, rect.y + margin,
                                  8, rect.height - 2 * margin))
                pygame.draw.rect(surface, icon_color,
                                 (rect.right - margin - 8, rect.y + margin,
                                  8, rect.height - 2 * margin))
            else:  # Play
                # Треугольник, направленный вправо
                pygame.draw.polygon(surface, icon_color, [
                    (rect.x + margin, rect.y + margin),
                    (rect.x + margin, rect.bottom - margin),
                    (rect.right - margin, rect.centery)
                ])

        elif btn_type == 'next':
            # Двойная стрелка вправо
            # Первый треуголник
            pygame.draw.polygon(surface, icon_color, [
                (rect.right - margin, rect.centery),
                (rect.right - margin - 15, rect.y + margin),
                (rect.right - margin - 15, rect.bottom - margin)
            ])

            # Второй треугольник (с отступом)
            pygame.draw.polygon(surface, icon_color, [
                (rect.right - margin - 20, rect.centery),
                (rect.right - margin - 35, rect.y + margin),
                (rect.right - margin - 35, rect.bottom - margin)
            ])

        # Добавляем эффект свечения при наведении
        if self.player_buttons[btn_type].collidepoint(pygame.mouse.get_pos()):
            glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*icon_color, 30), glow.get_rect(), border_radius=5)
            surface.blit(glow, rect)

    def _draw_track_name(self, surface: pygame.Surface, y_pos: int) -> None:
        """Отрисовка названия текущего трека с эффектом прокрутки"""
        track_name = "Current Track Name"  # Здесь нужно получить реальное название
        text_width = FONT_SMALL.size(track_name)[0]
        max_width = self.window_width - 40

        if text_width > max_width:
            # Эффект бегущей строки
            self.music_track_scroll = (self.music_track_scroll + 1) % (text_width + 50)

            text_surface = FONT_SMALL.render(track_name, True, WHITE)
            scroll_surface = pygame.Surface((max_width, 30), pygame.SRCALPHA)

            # Основной текст
            scroll_surface.blit(text_surface, (-self.music_track_scroll, 0))
            # Повтор текста для плавности
            scroll_surface.blit(text_surface, (text_width - self.music_track_scroll + 50, 0))

            surface.blit(scroll_surface, (self.window_rect.x + 20, y_pos))
        else:
            # Просто центрированный текст
            text = FONT_SMALL.render(track_name, True, WHITE)
            surface.blit(text, (self.window_rect.centerx - text.get_width() // 2, y_pos))

    def _draw_player_icon(self, surface: pygame.Surface, btn_type: str, rect: pygame.Rect) -> None:
        """Отрисовка иконок для кнопок плеера"""
        icon_color = WHITE
        margin = 10
        line_width = 3  # Толщина линий для векторных иконок

        if btn_type == 'shuffle':
            # Иконка перемешивания (две стрелки)
            # Левая стрелка
            pygame.draw.line(surface, icon_color,
                             (rect.x + margin + 5, rect.centery + 5),
                             (rect.x + margin, rect.centery), line_width)
            pygame.draw.line(surface, icon_color,
                             (rect.x + margin, rect.centery),
                             (rect.x + margin + 5, rect.centery - 5), line_width)

            # Правая стрелка
            pygame.draw.line(surface, icon_color,
                             (rect.right - margin - 5, rect.centery - 5),
                             (rect.right - margin, rect.centery), line_width)
            pygame.draw.line(surface, icon_color,
                             (rect.right - margin, rect.centery),
                             (rect.right - margin - 5, rect.centery + 5), line_width)

            # Волнообразная линия между стрелками
            wave_points = [
                (rect.x + margin + 10, rect.centery + 3),
                (rect.centerx - 10, rect.centery - 2),
                (rect.centerx, rect.centery + 4),
                (rect.centerx + 10, rect.centery - 3)
            ]
            pygame.draw.lines(surface, icon_color, False, wave_points, line_width)

        elif btn_type == 'prev':
            # Двойная стрелка влево
            # Первый треуголник
            pygame.draw.polygon(surface, icon_color, [
                (rect.x + margin, rect.centery),
                (rect.x + margin + 15, rect.y + margin),
                (rect.x + margin + 15, rect.bottom - margin)
            ])

            # Второй треугольник (с отступом)
            pygame.draw.polygon(surface, icon_color, [
                (rect.x + margin + 20, rect.centery),
                (rect.x + margin + 35, rect.y + margin),
                (rect.x + margin + 35, rect.bottom - margin)
            ])

        elif btn_type == 'play':
            if pygame.mixer.music.get_busy():  # Пауза
                # Две вертикальные линии
                pygame.draw.rect(surface, icon_color,
                                 (rect.x + margin, rect.y + margin,
                                  8, rect.height - 2 * margin))
                pygame.draw.rect(surface, icon_color,
                                 (rect.right - margin - 8, rect.y + margin,
                                  8, rect.height - 2 * margin))
            else:  # Play
                # Треугольник, направленный вправо
                pygame.draw.polygon(surface, icon_color, [
                    (rect.x + margin, rect.y + margin),
                    (rect.x + margin, rect.bottom - margin),
                    (rect.right - margin, rect.centery)
                ])

        elif btn_type == 'next':
            # Двойная стрелка вправо
            # Первый треуголник
            pygame.draw.polygon(surface, icon_color, [
                (rect.right - margin, rect.centery),
                (rect.right - margin - 15, rect.y + margin),
                (rect.right - margin - 15, rect.bottom - margin)
            ])

            # Второй треугольник (с отступом)
            pygame.draw.polygon(surface, icon_color, [
                (rect.right - margin - 20, rect.centery),
                (rect.right - margin - 35, rect.y + margin),
                (rect.right - margin - 35, rect.bottom - margin)
            ])

        # Добавляем эффект свечения при наведении
        if self.player_buttons[btn_type].collidepoint(pygame.mouse.get_pos()):
            glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*icon_color, 30), glow.get_rect(), border_radius=5)
            surface.blit(glow, rect)

    def _draw_save_button(self, surface: pygame.Surface) -> None:
        """Отрисовка кнопки сохранения"""
        is_hovered = self.save_btn.collidepoint(pygame.mouse.get_pos())
        color = GREEN if not is_hovered else GREEN_HOVER  # Используем глобальные цветовые константы

        # Рисуем кнопку с закругленными углами
        pygame.draw.rect(surface, color, self.save_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.save_btn, 1, border_radius=5)  # Рамка

        # Получаем локализованный текст для кнопки
        save_text = self.locale.get('ui.save')
        btn_text = FONT_SMALL.render(save_text, True, WHITE)

        # Центрируем текст на кнопке
        surface.blit(
            btn_text,
            (
                self.save_btn.centerx - btn_text.get_width() // 2,
                self.save_btn.centery - btn_text.get_height() // 2
            )
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Обработка событий интерфейса"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                return self._handle_click(event.pos)

            elif event.button == 4:  # Колесо мыши вверх
                self.scroll_offset = min(0, self.scroll_offset + 10)
                return "scroll"

            elif event.button == 5:  # Колесо мыши вниз
                self.scroll_offset = max(-(self.total_height - self.window_height),
                                         self.scroll_offset - 10)
                return "scroll"

        elif event.type == pygame.MOUSEMOTION:
            if self.volume_slider['dragging']:
                self._update_volume_from_slider(event.pos[0])
                return "volume_changed"

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.volume_slider['dragging']:
                self.volume_slider['dragging'] = False
                return "volume_changed"

        return None

    def _handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Обработка кликов по элементам UI"""
        # Кнопка закрытия
        if self.close_btn.collidepoint(pos):
            return "close"

        # Ползунок громкости
        if self.volume_slider['handle_rect'].collidepoint(pos):
            self.volume_slider['dragging'] = True
            return "volume_drag_start"

        if self.volume_slider['rect'].collidepoint(pos):
            self._update_volume_from_slider(pos[0])
            return "volume_changed"

        # Кнопки плеера
        for btn_type, btn_rect in self.player_buttons.items():
            if btn_rect.collidepoint(pos):
                return f"music_{btn_type}"

        # Переключатели
        for key, data in self.toggle_buttons.items():
            if data['rect'].collidepoint(pos):
                self.toggle_buttons[key]['state'] = not data['state']
                return f"toggle_{key}"

        # Кнопка сохранения
        if self.save_btn.collidepoint(pos):
            return "save"

        return None

    def _update_volume_from_slider(self, mouse_x: int) -> None:
        """Обновление громкости на основе позиции ползунка"""
        slider = self.volume_slider['rect']
        handle = self.volume_slider['handle_rect']

        # Вычисляем новую позицию
        new_x = max(slider.left, min(slider.right, mouse_x))
        handle.centerx = new_x

        # Обновляем значение громкости
        volume = (new_x - slider.left) / slider.width
        self.config.set('music_volume', volume)

    def set_language(self, language: str) -> None:
        """Установка языка интерфейса"""
        self.language = language

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_particles(self, pos, count=20):
        """Добавляет частицы в указанной позиции"""
        for _ in range(count):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(1, 5)
            self.particles.append([
                pos[0], pos[1],  # x, y
                math.cos(angle) * speed, math.sin(angle) * speed,  # velocity x, y
                random.randint(1, 3),  # size
                random.randint(10, 30)  # lifetime
            ])

    def update(self):
        """Обновляет состояние частиц"""
        for p in self.particles[:]:
            p[0] += p[2]  # update x position
            p[1] += p[3]  # update y position
            p[5] -= 1  # decrease lifetime

            if p[5] <= 0:
                self.particles.remove(p)

    def draw(self, surface, color):
        """Отрисовывает частицы"""
        for p in self.particles:
            pygame.draw.circle(surface, color, (int(p[0]), int(p[1])), p[4])

class ShakeEffect:
    def __init__(self):
        self.offset = [0, 0]
        self.intensity = 0
        self.duration = 0

    def start(self, intensity=3, duration=10):
        """Запускает эффект дрожания"""
        self.intensity = intensity
        self.duration = duration

    def update(self):
        """Обновляет эффект дрожания"""
        if self.duration > 0:
            self.offset[0] = random.randint(-self.intensity, self.intensity)
            self.offset[1] = random.randint(-self.intensity, self.intensity)
            self.duration -= 1
        else:
            self.offset = [0, 0]

    def apply(self, pos):
        """Применяет смещение к позиции"""
        return (pos[0] + self.offset[0], pos[1] + self.offset[1])

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text_key: str,
                 action: Optional[callable] = None, locale: Optional[Locale] = None):
        """
        Инициализация кнопки с поддержкой локализации

        :param x: Позиция X
        :param y: Позиция Y
        :param width: Ширина кнопки
        :param height: Высота кнопки
        :param text_key: Ключ текста для локализации
        :param action: Функция, вызываемая при клике
        :param locale: Объект локализации
        """
        self.original_rect = pygame.Rect(x, y, width, height)
        self.rect = self.original_rect.copy()
        self.text_key = text_key
        self.action = action
        self.locale = locale
        self.is_hovered = False
        self.is_pressed = False
        self.current_size = 1.0
        self.target_size = 1.0
        self.glow_alpha = 0
        self.pulse_speed = 0.05
        self.animation_time = 0

        # Цвета для разных состояний
        self.colors = {
            'normal': BLUE_BUTTON,
            'hover': BLUE_BUTTON_HOVER,
            'pressed': (100, 100, 255),
            'text': WHITE,
            'border': WHITE
        }

        # Звуковые эффекты
        self.hover_sound = None
        self.click_sound = None

    def set_locale(self, locale: Locale) -> None:
        """Установка объекта локализации"""
        self.locale = locale

    def set_sounds(self, hover_sound: Optional[pygame.mixer.Sound],
                   click_sound: Optional[pygame.mixer.Sound]) -> None:
        """Установка звуков для кнопки"""
        self.hover_sound = hover_sound
        self.click_sound = click_sound

    def update(self, dt: float) -> None:
        """Обновление анимации кнопки"""
        self.animation_time += dt

        # Плавное изменение размера при наведении
        target_scale = 1.05 if self.is_hovered else 1.0
        self.current_size += (target_scale - self.current_size) * 0.2

        # Эффект пульсации
        pulse = math.sin(self.animation_time * 3) * 0.02 if self.is_hovered else 0
        self.target_size = target_scale + pulse

        # Эффект свечения
        target_glow = 30 if self.is_hovered else 0
        self.glow_alpha += (target_glow - self.glow_alpha) * 0.1

        # Обновление прямоугольника с учетом анимации
        new_width = int(self.original_rect.width * self.current_size)
        new_height = int(self.original_rect.height * self.current_size)
        self.rect.width = new_width
        self.rect.height = new_height
        self.rect.center = self.original_rect.center

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка кнопки"""
        # Определение цвета в зависимости от состояния
        if self.is_pressed:
            color = self.colors['pressed']
        elif self.is_hovered:
            color = self.colors['hover']
        else:
            color = self.colors['normal']

        # Рисуем основной прямоугольник
        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        # Рисуем свечение при наведении
        if self.glow_alpha > 0:
            glow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*WHITE, int(self.glow_alpha)),
                             glow.get_rect(), border_radius=10)
            surface.blit(glow, self.rect)

        # Рисуем обводку
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2, border_radius=10)

        # Получаем локализованный текст
        text = self.locale.get(self.text_key) if self.locale else f"[{self.text_key}]"

        # Рисуем текст с учетом масштабирования
        font_size = int(16 * self.current_size)
        font = pygame.font.SysFont("Courier New", font_size, bold=True)
        text_surf = font.render(text, True, self.colors['text'])
        text_rect = text_surf.get_rect(center=self.rect.center)

        # Небольшое смещение текста при нажатии
        if self.is_pressed:
            text_rect.y += 2

        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Обработка событий кнопки
        Возвращает True, если было взаимодействие с кнопкой
        """
        if event.type == pygame.MOUSEMOTION:
            # Проверка наведения
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)

            # Воспроизведение звука при наведении
            if not was_hovered and self.is_hovered and self.hover_sound:
                self.hover_sound.play()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_pressed = True
                if self.click_sound:
                    self.click_sound.play()
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.is_hovered:
                self.is_pressed = False
                if self.action:
                    self.action()
                return True
            self.is_pressed = False

        return False

    def check_hover(self, pos: Tuple[int, int]) -> bool:
        """Проверка наведения мыши с обновлением состояния"""
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

class SaveManager:
    def __init__(self, save_file: str = SAVE_FILE, locale: Optional[Locale] = None):
        self.save_file = Path(__file__).parent / save_file
        self.locale = locale or Locale()
        self.default_data = {
            "game_state": GameState.MENU,
            "player_stats": {
                "courage": 0,
                "ptsd": 0,
                "promiscuity": 0,
                "narcissism": 0
            },
            "inventory": [],
            "achievements": [],
            "settings": {
                "music_volume": 0.7,
                "sound_volume": 0.7,
                "fullscreen": False,
                "language": "ru",
                "resolution": (SCREEN_WIDTH, SCREEN_HEIGHT),
                "text_speed": 1.0
            },
            "story_progress": 0,
            "last_played": None
        }

    def load_save(self) -> Dict[str, Any]:
        """Загружает сохранение из файла"""
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Проверяем наличие всех необходимых ключей
                for key in self.default_data:
                    if key not in data:
                        data[key] = self.default_data[key]
                return data
        except FileNotFoundError:
            print(self.locale.get("settings_manager.file_not_found"))
            return self.default_data
        except json.JSONDecodeError:
            print(self.locale.get("settings_manager.load_error_json"))
            return self.default_data
        except IOError:
            print(self.locale.get("settings_manager.load_error_io"))
            return self.default_data

    def save_game(self, data: Dict[str, Any]) -> bool:
        """Сохраняет текущее состояние игры"""
        try:
            # Убедимся, что все необходимые ключи присутствуют
            for key in self.default_data:
                if key not in data:
                    data[key] = self.default_data[key]

            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(self.locale.get("settings_manager.save_success"))
            return True
        except IOError:
            print(self.locale.get("settings_manager.save_error"))
            return False

    def reset_to_defaults(self) -> Dict[str, Any]:
        """Сбрасывает сохранение к значениям по умолчанию"""
        print(self.locale.get("settings_manager.reset_success"))
        return self.default_data

    def delete_save(self) -> bool:
        """Удаляет файл сохранения"""
        try:
            self.save_file.unlink()
            return True
        except FileNotFoundError:
            return True  # Файла нет - значит уже удален
        except Exception:
            return False

    def get_save_info(self) -> Dict[str, Any]:
        """Возвращает информацию о сохранении без загрузки всех данных"""
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    "exists": True,
                    "last_played": data.get("last_played"),
                    "story_progress": data.get("story_progress", 0),
                    "player_stats": data.get("player_stats", {})
                }
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            return {
                "exists": False,
                "last_played": None,
                "story_progress": 0,
                "player_stats": {}
            }

    def add_to_inventory(self, item: str):
        """Добавляет предмет в инвентарь"""
        if item not in self.current_data["inventory"]:
            self.current_data["inventory"].append(item)

    def remove_from_inventory(self, item: str) -> bool:
        """Удаляет предмет из инвентаря, возвращает True если успешно"""
        if item in self.current_data["inventory"]:
            self.current_data["inventory"].remove(item)
            return True
        return False

    def unlock_action(self, action: str):
        """Добавляет новое доступное действие"""
        if action not in self.current_data["actions"]:
            self.current_data["actions"].append(action)

    def complete_action(self, action: str) -> bool:
        """
        Помечает действие как выполненное (и недоступное для повторного использования)
        Возвращает True если действие было доступно
        """
        if action in self.current_data["actions"]:
            self.current_data["actions"].remove(action)
            self.current_data["completed_actions"].add(action)
            return True
        return False

    def set_story_flag(self, flag: str, value: any = True):
        """Устанавливает флаг истории (для развилок)"""
        self.current_data["story_flags"][flag] = value

    def get_story_flag(self, flag: str, default=None) -> any:
        """Получает значение флага истории"""
        return self.current_data["story_flags"].get(flag, default)

    def reset_game(self):
        """Сбрасывает состояние игры к начальному"""
        self.current_data = self.default_data.copy()
        if os.path.exists(self.save_file):
            os.remove(self.save_file)

    def get_available_actions(self) -> List[str]:
        """Возвращает список доступных действий"""
        return self.current_data["actions"].copy()

    def get_inventory(self) -> List[str]:
        """Возвращает список предметов в инвентаре"""
        return self.current_data["inventory"].copy()

    def get_completed_actions(self) -> Set[str]:
        """Возвращает множество выполненных действий"""
        return self.current_data["completed_actions"].copy()

    def set_current_dialog(self, dialog_id: str):
        """Устанавливает текущий диалог"""
        self.current_data["current_dialog"] = dialog_id

    def get_current_dialog(self) -> str:
        """Получает текущий диалог"""
        return self.current_data["current_dialog"]

    def update_character_stat(self, stat: str, change: int):
        """Изменяет характеристику персонажа"""
        if stat in self.current_data["character_stats"]:
            self.current_data["character_stats"][stat] = max(0, min(100,
                                                                    self.current_data["character_stats"][
                                                                        stat] + change))

    def get_character_stats(self) -> Dict[str, int]:
        """Возвращает текущие характеристики персонажа"""
        return self.current_data["character_stats"].copy()

class CentralImageManager:
    """Класс для управления центральным изображением"""

    def __init__(self):
        self.central_images = []  # Основные изображения
        self.special_images = {}  # Специальные изображения
        self.current_image_index = 0  # Текущий индекс изображения
        self.last_image_change_time = pygame.time.get_ticks()  # Время последней смены изображения
        self.last_click_time = pygame.time.get_ticks()  # Время последнего клика
        self.image_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 250, 500,
                                      500)  # Прямоугольник изображения
        self.is_hovered = False  # Наведена ли мышь
        self.showing_special = False  # Показывается ли спец. изображение
        self.return_to_cycle = False  # Возврат к циклу изображений

        self.load_images()

    def load_images(self):
        """Загрузка всех изображений"""
        # Загрузка основных изображений (1-3)
        for i in range(1, 4):
            try:
                img = pygame.image.load(f'pics/image{i}.jpg').convert()
                img_with_alpha = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                img_with_alpha.blit(img, (0, 0))
                img_with_alpha = self.remove_black_background(img_with_alpha)
                img_with_alpha = pygame.transform.scale(img_with_alpha, (500, 500))
                self.central_images.append(img_with_alpha)
            except Exception as e:
                print(f"Ошибка загрузки image{i}.jpg:", e)
                img = self.create_placeholder_image(f"Изображение {i}")
                self.central_images.append(img)

        # Загрузка специальных изображений
        for i, name in [(4, "timeout"), (5, "hover")]:
            try:
                img = pygame.image.load(f'pics/image{i}.jpg').convert()
                img_with_alpha = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                img_with_alpha.blit(img, (0, 0))
                img_with_alpha = self.remove_black_background(img_with_alpha)
                img_with_alpha = pygame.transform.scale(img_with_alpha, (500, 500))
                self.special_images[name] = img_with_alpha
            except Exception as e:
                print(f"Ошибка загрузки image{i}.jpg:", e)
                img = self.create_placeholder_image(f"Спец. {i}")
                self.special_images[name] = img

    def create_placeholder_image(self, text):
        """Создание заглушки для изображения"""
        img = pygame.Surface((500, 500), pygame.SRCALPHA)
        pygame.draw.rect(img, (50, 50, 100, 200), (0, 0, 500, 500))
        font = pygame.font.SysFont("Courier New", 36, bold=True)
        text_surface = font.render(text, True, WHITE)
        img.blit(text_surface, (250 - text_surface.get_width() // 2, 250 - text_surface.get_height() // 2))
        return img

    def remove_black_background(self, surface, threshold=30):
        """Удаление черного фона у изображения"""
        result = surface.copy()
        result.lock()
        for x in range(result.get_width()):
            for y in range(result.get_height()):
                color = result.get_at((x, y))
                if color.r < threshold and color.g < threshold and color.b < threshold:
                    result.set_at((x, y), (0, 0, 0, 0))
        result.unlock()
        return result

    def update(self):
        """Обновление состояния изображения"""
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        hover_image = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 100, 200, 200)
        self.is_hovered = hover_image.collidepoint(mouse_pos)

        # Смена изображения каждые 500мс, если не показывается спец. изображение
        if current_time - self.last_image_change_time > 500 and not self.return_to_cycle:
            self.current_image_index = (self.current_image_index + 1) % len(self.central_images)
            self.last_image_change_time = current_time

    def draw(self, surface):
        """Отрисовка текущего изображения"""
        if self.is_hovered and "hover" in self.special_images and not self.return_to_cycle:
            surface.blit(self.special_images["hover"], self.image_rect)
            self.showing_special = True
        else:
            surface.blit(self.central_images[self.current_image_index], self.image_rect)
            self.showing_special = False

class StatsPanel:
    """Панель статистики персонажа"""

    def __init__(self, save_system, locale):
        self.save_system = save_system
        self.locale = locale
        self.panel_rect = pygame.Rect(SCREEN_WIDTH - 230, 50, 200, SCREEN_HEIGHT - 300)
        self.stat_colors = {
            "Отвага": (0, 200, 0),
            "ПТСР": (200, 0, 0),
            "Блядство": (0, 100, 200),
            "ЧСВ": (200, 200, 0)
        }

    def draw(self, surface, font):
        """Отрисовка панели статистики"""
        pygame.draw.rect(surface, UI_PANEL_BG, self.panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.panel_rect, 2, border_radius=10)

        title = font.render(self.locale.get("ui.stats_title"), True, WHITE)
        surface.blit(title, (self.panel_rect.x + 10, self.panel_rect.y + 10))

        y_offset = 50
        stats = self.save_system.get_character_stats()
        for stat, value in stats.items():
            # Название характеристики
            stat_text = font.render(stat, True, WHITE)
            surface.blit(stat_text, (self.panel_rect.x + 15, self.panel_rect.y + y_offset))

            # Полоска характеристики
            bar_width = 170
            filled_width = (value / 100) * bar_width
            pygame.draw.rect(surface, (50, 50, 80),
                             (self.panel_rect.x + 15, self.panel_rect.y + y_offset + 25, bar_width, 15))
            pygame.draw.rect(surface, self.stat_colors.get(stat, WHITE),
                             (self.panel_rect.x + 15, self.panel_rect.y + y_offset + 25, filled_width, 15))

            # Значение характеристики
            value_text = font.render(f"{value}%", True, WHITE)
            surface.blit(value_text,
                         (self.panel_rect.x + bar_width - value_text.get_width() + 15,
                          self.panel_rect.y + y_offset + 25))

            y_offset += 50

class ActionsPanel:
    """Панель действий"""

    def __init__(self, locale):
        self.locale = locale
        self.act_btn = pygame.Rect(60, SCREEN_HEIGHT - 540, 130, 30)  # Кнопка действий
        self.inv_btn = pygame.Rect(60, SCREEN_HEIGHT - 500, 130, 30)  # Кнопка инвентаря
        self.sett_btn = pygame.Rect(60, SCREEN_HEIGHT - 460, 130, 30)  # Кнопка настроек

        self.act_hovered = False  # Наведение на кнопку действий
        self.inv_hovered = False  # Наведение на кнопку инвентаря
        self.sett_hovered = False  # Наведение на кнопку настроек

    def draw(self, surface, font):
        """Отрисовка панели действий"""
        panel_rect = pygame.Rect(50, 50, 150, SCREEN_HEIGHT - 470)
        pygame.draw.rect(surface, UI_PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)

        # Кнопка действий
        btn_color = UI_BUTTON_HOVER if self.act_hovered else UI_BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, self.act_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.act_btn, 1, border_radius=5)
        text = font.render(self.locale.get("ui.actions"), True, WHITE)
        surface.blit(text, (self.act_btn.centerx - text.get_width() // 2,
                            self.act_btn.centery - text.get_height() // 2))

        # Кнопка инвентаря
        btn_color = UI_BUTTON_HOVER if self.inv_hovered else UI_BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, self.inv_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.inv_btn, 1, border_radius=5)
        text = font.render(self.locale.get("ui.inventory"), True, WHITE)
        surface.blit(text, (self.inv_btn.centerx - text.get_width() // 2,
                            self.inv_btn.centery - text.get_height() // 2))

        # Кнопка настроек
        btn_color = UI_BUTTON_HOVER if self.sett_hovered else UI_BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, self.sett_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.sett_btn, 1, border_radius=5)
        text = font.render(self.locale.get("ui.settings"), True, WHITE)
        surface.blit(text, (self.sett_btn.centerx - text.get_width() // 2,
                            self.sett_btn.centery - text.get_height() // 2))

    def check_hover(self, pos):
        """Проверка наведения на кнопки"""
        self.act_hovered = self.act_btn.collidepoint(pos)
        self.inv_hovered = self.inv_btn.collidepoint(pos)
        self.sett_hovered = self.sett_btn.collidepoint(pos)

class ActionsWindow:
    """Окно действий"""

    def __init__(self, save_system, locale):
        self.save_system = save_system
        self.locale = locale
        self.show = False  # Видимость окна
        self.act_close_btn = pygame.Rect(0, 0, 30, 30)  # Кнопка закрытия
        self.act_close_hovered = False  # Наведение на кнопку закрытия

    def draw(self, surface, font):
        """Отрисовка окна действий"""
        if not self.show:
            return

        act_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 200, 400, 400)
        pygame.draw.rect(surface, (20, 20, 50), act_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, act_rect, 2, border_radius=10)

        title = font.render(self.locale.get("ui.actions_title"), True, WHITE)
        surface.blit(title, (act_rect.centerx - title.get_width() // 2, act_rect.y + 20))

        # Отрисовка доступных действий
        actions = self.save_system.get_available_actions()
        y_offset = 70
        for action in actions:
            action_rect = pygame.Rect(act_rect.x + 20, act_rect.y + y_offset, 360, 30)
            is_hovered = action_rect.collidepoint(pygame.mouse.get_pos())

            btn_color = UI_BUTTON_HOVER if is_hovered else UI_BUTTON_COLOR
            pygame.draw.rect(surface, btn_color, action_rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, action_rect, 1, border_radius=5)

            text = font.render(action, True, WHITE)
            surface.blit(text, (action_rect.x + 10, action_rect.y + 5))
            y_offset += 40

        # Кнопка закрытия
        self.act_close_btn.update(act_rect.right - 40, act_rect.y + 10, 30, 30)
        btn_color = (230, 80, 80) if self.act_close_hovered else (200, 50, 50)
        pygame.draw.rect(surface, btn_color, self.act_close_btn, border_radius=15)
        close_text = font.render("X", True, WHITE)
        surface.blit(close_text, (self.act_close_btn.centerx - close_text.get_width() // 2,
                                  self.act_close_btn.centery - close_text.get_height() // 2))

    def check_hover(self, pos):
        """Проверка наведения на кнопку закрытия"""
        self.act_close_hovered = self.act_close_btn.collidepoint(pos) if self.show else False

    def handle_click(self, pos):
        """Обработка кликов в окне действий"""
        if not self.show:
            return False

        if self.act_close_btn.collidepoint(pos):
            self.show = False
            return True
        return False

class InventoryWindow:
    """Окно инвентаря"""

    def __init__(self, save_system, locale):
        self.save_system = save_system
        self.locale = locale
        self.show = False  # Видимость окна
        self.inv_close_btn = pygame.Rect(0, 0, 30, 30)  # Кнопка закрытия
        self.inv_close_hovered = False  # Наведение на кнопку закрытия

    def draw(self, surface, font):
        """Отрисовка окна инвентаря"""
        if not self.show:
            return

        inv_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 200, 400, 400)
        pygame.draw.rect(surface, (20, 20, 50), inv_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, inv_rect, 2, border_radius=10)

        title = font.render(self.locale.get("ui.inventory_title"), True, WHITE)
        surface.blit(title, (inv_rect.centerx - title.get_width() // 2, inv_rect.y + 20))

        # Отрисовка предметов инвентаря
        inventory = self.save_system.get_inventory()
        y_offset = 70
        for item in inventory:
            text = font.render(item, True, WHITE)
            surface.blit(text, (inv_rect.x + 20, inv_rect.y + y_offset))
            y_offset += 30

        # Кнопка закрытия
        self.inv_close_btn.update(inv_rect.right - 40, inv_rect.y + 10, 30, 30)
        btn_color = (230, 80, 80) if self.inv_close_hovered else (200, 50, 50)
        pygame.draw.rect(surface, btn_color, self.inv_close_btn, border_radius=15)
        close_text = font.render("X", True, WHITE)
        surface.blit(close_text, (self.inv_close_btn.centerx - close_text.get_width() // 2,
                                  self.inv_close_btn.centery - close_text.get_height() // 2))

    def check_hover(self, pos):
        """Проверка наведения на кнопку закрытия"""
        self.inv_close_hovered = self.inv_close_btn.collidepoint(pos) if self.show else False

    def handle_click(self, pos):
        """Обработка кликов в окне инвентаря"""
        if not self.show:
            return False

        if self.inv_close_btn.collidepoint(pos):
            self.show = False
            return True
        return False

class GameUI:
    """Основной класс пользовательского интерфейса"""

    def __init__(self, save_system, dialog_manager, settings):
        self.locale = Locale()  # Локализация
        self.save_system = save_system  # Система сохранений
        self.dialog_manager = dialog_manager  # Менеджер диалогов
        self.settings = settings  # Настройки

        # Инициализация компонентов
        self.central_image = CentralImageManager()  # Центральное изображение
        self.stats_panel = StatsPanel(save_system, self.locale)  # Панель статистики
        self.actions_panel = ActionsPanel(self.locale)  # Панель действий
        self.actions_window = ActionsWindow(save_system, self.locale)  # Окно действий
        self.inventory_window = InventoryWindow(save_system, self.locale)  # Окно инвентаря

        # Состояние UI
        self.last_click_pos = None  # Позиция последнего клика

    def draw(self, surface):
        """Отрисовка всех элементов интерфейса"""
        # Полупрозрачный фон
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        surface.blit(s, (0, 0))

        # Отрисовка компонентов
        self.central_image.draw(surface)
        self.stats_panel.draw(surface, FONT_SMALL)
        self.actions_panel.draw(surface, FONT_SMALL)

        # Отрисовка окон, если они видимы
        self.actions_window.draw(surface, FONT_SMALL)
        self.inventory_window.draw(surface, FONT_SMALL)

        # Всегда отрисовываем диалоги
        self.dialog_manager.draw(surface)

    def handle_click(self, pos):
        """Обработка кликов мыши"""
        # Сначала проверяем диалоги
        if self.dialog_manager.handle_click(pos):
            return True

        self.last_click_pos = pos

        # Проверка кнопок панели
        if self.actions_panel.act_btn.collidepoint(pos):
            self.actions_window.show = not self.actions_window.show
            self.inventory_window.show = False
            return True
        elif self.actions_panel.inv_btn.collidepoint(pos):
            self.inventory_window.show = not self.inventory_window.show
            self.actions_window.show = False
            return True
        elif self.actions_panel.sett_btn.collidepoint(pos):
            # Обработка кнопки настроек
            return True

        # Проверка кнопок закрытия окон
        if self.actions_window.handle_click(pos):
            return True
        if self.inventory_window.handle_click(pos):
            return True

        return False

    def check_hover(self, pos):
        """Проверка наведения на элементы интерфейса"""
        self.actions_panel.check_hover(pos)
        self.actions_window.check_hover(pos)
        self.inventory_window.check_hover(pos)

    def update(self):
        """Обновление состояния интерфейса"""
        self.central_image.update()

class DialogManager:
    def __init__(self, locale: 'Locale', save_system: 'SaveManager'):
        # Основные параметры диалогового окна
        self.dialog_rect = pygame.Rect(50, 600 - 150, 800 - 100, 140)
        self.locale = locale
        self.save_system = save_system

        # Текущее состояние диалога
        self.current_dialog: List[Dict] = []
        self.current_text: str = ""
        self.char_index: int = 0
        self.text_speed: int = 1
        self.last_update: int = 0
        self.update_delay: int = 30

        # Система выбора
        self.question: Optional[str] = None
        self.choices: List[Dict] = []
        self.choice_rects: List[pygame.Rect] = []
        self.choice_result: Optional[str] = None
        self.waiting_for_choice: bool = False

        # Информация о говорящем
        self.speaker: Optional[str] = None
        self.speaker_image: Optional[pygame.Surface] = None
        self.show_dialog: bool = True

        # Прокрутка текста
        self.scrolling_texts: Dict = {}
        self.scroll_pos: int = 0
        self.scroll_speed: int = 2
        self.last_scroll_time: int = 0

        # История диалогов
        self.dialog_history: List[Dict] = []

        # Концовки
        self.is_show_ending: bool = False
        self.current_ending: Optional[str] = None

        # Загрузка диалогов
        self.dialogs: Dict = self.load_dialogs()

        # Шрифты (должны быть инициализированы в основном коде)
        self.font_small = pygame.font.SysFont("Courier New", 16)
        self.font_medium = pygame.font.SysFont("Courier New", 24)
        self.font_large = pygame.font.SysFont("Courier New", 36)

        # Цвета
        self.COLORS = {
            'dialog_bg': (20, 20, 50, 220),
            'choice_bg': (30, 30, 70, 240),
            'button': (50, 50, 150),
            'button_hover': (70, 70, 200),
            'white': (223, 223, 223),
            'yellow': (255, 255, 0)
        }

    def load_dialogs(self) -> Dict:
        """Загружает диалоги из файла story.json"""
        try:
            with open('story.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading dialogs: {e}")
            return self._create_default_dialogs()

    def _create_default_dialogs(self) -> Dict:
        """Создает стандартные диалоги, если файл не найден"""
        return {
            "start": {
                "ru": [
                    {"text": "Приветствую, странник.", "speaker": "npc1"},
                    {"text": "Ты попал в странное место...", "speaker": "npc1"},
                    {
                        "text": "Что будешь делать?",
                        "speaker": "npc1",
                        "choices": [
                            {"text": "Исследовать", "next": "explore"},
                            {"text": "Сражаться", "next": "fight"},
                            {"text": "Уйти", "next": "leave"}
                        ]
                    }
                ],
                "en": [
                    {"text": "Greetings, wanderer.", "speaker": "npc1"},
                    {"text": "You've come to a strange place...", "speaker": "npc1"},
                    {
                        "text": "What will you do?",
                        "speaker": "npc1",
                        "choices": [
                            {"text": "Explore", "next": "explore"},
                            {"text": "Fight", "next": "fight"},
                            {"text": "Leave", "next": "leave"}
                        ]
                    }
                ]
            }
        }

    def start_dialog(self, dialog_id: str, language: str = "ru") -> None:
        """Начинает новый диалог по идентификатору"""
        self.dialog_history = []

        if dialog_id not in self.dialogs or language not in self.dialogs[dialog_id]:
            print(f"Dialog {dialog_id} not found for language {language}")
            return

        dialog_data = self.dialogs[dialog_id][language]
        self.current_dialog = dialog_data.copy()
        self.next()

    def update(self) -> None:
        """Обновляет состояние диалога (постепенное появление текста)"""
        current_time = pygame.time.get_ticks()

        if (self.current_text and
                self.char_index < len(self.current_text) and
                current_time - self.last_update > self.update_delay):

            self.char_index += self.text_speed
            if self.char_index > len(self.current_text):
                self.char_index = len(self.current_text)
            self.last_update = current_time

    def next(self) -> None:
        """Переходит к следующей реплике в диалоге"""
        if self.char_index < len(self.current_text):
            self.char_index = len(self.current_text)
            return

        if self.waiting_for_choice:
            return

        if not self.current_dialog:
            self.current_text = ""
            self.question = None
            self.choices = []
            return

        dialog = self.current_dialog.pop(0)

        # Сохраняем текущий диалог в историю
        if self.current_text:
            self.dialog_history.append({
                "text": self.current_text,
                "speaker": self.speaker,
                "choices": self.choices.copy() if self.choices else None
            })

        self.current_text = dialog["text"]
        self.char_index = 0
        self.last_update = pygame.time.get_ticks()
        self.speaker = dialog.get("speaker")

        # Обработка специальных эффектов
        self._process_dialog_effects(dialog)

        # Обработка выбора
        if "choices" in dialog:
            self.question = self.current_text
            self.choices = dialog["choices"]
            self.choice_rects = []
            self.waiting_for_choice = True

    def _process_dialog_effects(self, dialog: Dict) -> None:
        """Обрабатывает эффекты, связанные с диалогом"""
        if "change_stats" in dialog:
            for stat, change in dialog["change_stats"].items():
                self.save_system.update_character_stat(stat, change)

        if "add_item" in dialog:
            self.save_system.add_to_inventory(dialog["add_item"])

        if "remove_item" in dialog:
            self.save_system.remove_from_inventory(dialog["remove_item"])

        if "unlock_action" in dialog:
            self.save_system.unlock_action(dialog["unlock_action"])

        if "set_flag" in dialog:
            flag, value = dialog["set_flag"]
            self.save_system.set_story_flag(flag, value)

        if "ending" in dialog:
            self.show_ending(dialog["ending"])

        if "next_scene" in dialog and not self.waiting_for_choice:
            self.start_scene(dialog["next_scene"])

    def previous(self) -> None:
        """Возвращается к предыдущей реплике в диалоге"""
        if self.char_index < len(self.current_text):
            self.char_index = len(self.current_text)
            return

        if not self.dialog_history or self.waiting_for_choice:
            return

        last_dialog = self.dialog_history.pop()

        if self.current_text:
            self.current_dialog.insert(0, {
                "text": self.current_text,
                "speaker": self.speaker,
                "choices": self.choices.copy() if self.choices else None
            })

        self.current_text = last_dialog["text"]
        self.char_index = len(self.current_text)
        self.speaker = last_dialog["speaker"]
        self.choices = last_dialog["choices"] if last_dialog["choices"] else []
        self.waiting_for_choice = bool(last_dialog["choices"])

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает диалоговое окно и связанные элементы"""
        if not self.show_dialog:
            return

        if self.is_show_ending:
            self._draw_ending(surface)
        else:
            self._draw_dialog_window(surface)

            if self.waiting_for_choice and self.char_index >= len(self.current_text):
                self._draw_choices(surface)

            if self.dialog_history:
                self._draw_back_button(surface)

    def _draw_dialog_window(self, surface: pygame.Surface) -> None:
        """Отрисовывает основное диалоговое окно"""
        dialog_surface = pygame.Surface((self.dialog_rect.width, self.dialog_rect.height), pygame.SRCALPHA)
        dialog_surface.fill(self.COLORS['dialog_bg'])

        visible_text = self.current_text[:self.char_index]
        lines = self._wrap_text(visible_text, self.font_small, self.dialog_rect.width - 40)

        y_offset = 20
        for line in lines:
            text_surface = self.font_small.render(line, True, self.COLORS['white'])
            dialog_surface.blit(text_surface, (20, y_offset))
            y_offset += self.font_small.get_linesize()

        if self.speaker:
            speaker_surface = self.font_small.render(self.speaker, True, self.COLORS['yellow'])
            dialog_surface.blit(speaker_surface, (20, 5))

        surface.blit(dialog_surface, self.dialog_rect)

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Разбивает текст на строки, чтобы он помещался в указанную ширину"""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "

        if current_line:
            lines.append(current_line)

        return lines

    def _draw_choices(self, surface: pygame.Surface) -> None:
        """Отрисовывает варианты выбора"""
        if not self.choices:
            return

        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        stats = self.save_system.get_character_stats()

        # Фильтрация доступных выборов по условиям
        available_choices = [
            choice for choice in self.choices
            if not choice.get("conditions") or all(
                stats.get(stat, 0) >= min_value
                for stat, min_value in choice["conditions"].items()
            )
        ]

        if not available_choices:
            self.waiting_for_choice = False
            return

        # Расчет размеров окна выбора
        choice_height = len(available_choices) * 40 + 40
        choice_rect = pygame.Rect(
            800 // 2 - 175,
            600 - 150 - choice_height - 30,
            350,
            choice_height
        )

        # Отрисовка фона выбора
        choice_surface = pygame.Surface((choice_rect.width, choice_rect.height), pygame.SRCALPHA)
        choice_surface.fill(self.COLORS['choice_bg'])

        y_offset = 10
        self.choice_buttons = []

        for i, choice in enumerate(available_choices):
            btn_rect = pygame.Rect(20, y_offset + i * 40 + 10, 310, 30)
            global_btn_rect = pygame.Rect(
                choice_rect.x + btn_rect.x,
                choice_rect.y + btn_rect.y,
                btn_rect.width,
                btn_rect.height
            )
            self.choice_buttons.append(global_btn_rect)

            is_hovered = global_btn_rect.collidepoint(mouse_pos)
            btn_color = self.COLORS['button_hover'] if is_hovered else self.COLORS['button']

            pygame.draw.rect(choice_surface, btn_color, btn_rect, border_radius=5)
            pygame.draw.rect(choice_surface, self.COLORS['white'], btn_rect, 1, border_radius=5)

            text = choice["text"]
            text_surface = self.font_small.render(text, True, self.COLORS['white'])

            # Обработка длинного текста с прокруткой
            if text_surface.get_width() > btn_rect.width - 20:
                if i not in self.scrolling_texts:
                    self.scrolling_texts[i] = {'offset': 0, 'last_update': current_time}

                scroll_speed = 3 if is_hovered else 1

                if current_time - self.scrolling_texts[i]['last_update'] > 50:
                    self.scrolling_texts[i]['offset'] -= scroll_speed
                    self.scrolling_texts[i]['last_update'] = current_time

                    if self.scrolling_texts[i]['offset'] < -text_surface.get_width():
                        self.scrolling_texts[i]['offset'] = btn_rect.width - 20

                visible_text = pygame.Surface((btn_rect.width - 20, text_surface.get_height()), pygame.SRCALPHA)
                visible_text.blit(text_surface, (self.scrolling_texts[i]['offset'], 0))

                if self.scrolling_texts[i]['offset'] < 0:
                    visible_text.blit(text_surface,
                                      (self.scrolling_texts[i]['offset'] + text_surface.get_width() + 20, 0))

                choice_surface.blit(
                    visible_text,
                    (btn_rect.x + 10, btn_rect.y + btn_rect.height // 2 - text_surface.get_height() // 2)
                )
            else:
                choice_surface.blit(
                    text_surface,
                    (
                        btn_rect.x + btn_rect.width // 2 - text_surface.get_width() // 2,
                        btn_rect.y + btn_rect.height // 2 - text_surface.get_height() // 2
                    )
                )

        surface.blit(choice_surface, choice_rect)

    def _draw_back_button(self, surface: pygame.Surface) -> None:
        """Отрисовывает кнопку 'Назад'"""
        back_btn = pygame.Rect(
            self.dialog_rect.x + 10,
            self.dialog_rect.y + self.dialog_rect.height - 30,
            60,
            20
        )

        pygame.draw.rect(surface, self.COLORS['button'], back_btn, border_radius=3)
        pygame.draw.rect(surface, self.COLORS['white'], back_btn, 1, border_radius=3)

        back_text = self.font_small.render("Назад", True, self.COLORS['white'])
        surface.blit(back_text, (back_btn.x + 10, back_btn.y + 5))

    def _draw_ending(self, surface: pygame.Surface) -> None:
        """Отрисовывает экран концовки"""
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        ending_rect = pygame.Rect(800 // 2 - 250, 600 // 2 - 150, 500, 300)
        pygame.draw.rect(surface, (30, 30, 60), ending_rect, border_radius=10)
        pygame.draw.rect(surface, self.COLORS['white'], ending_rect, 2, border_radius=10)

        title = self.font_large.render("КОНЦОВКА", True, self.COLORS['white'])
        surface.blit(title, (ending_rect.centerx - title.get_width() // 2, ending_rect.y + 20))

        ending_text = self.font_medium.render(self.current_ending, True, self.COLORS['white'])
        surface.blit(
            ending_text,
            (
                ending_rect.centerx - ending_text.get_width() // 2,
                ending_rect.centery - ending_text.get_height() // 2
            )
        )

        menu_btn = pygame.Rect(ending_rect.centerx - 100, ending_rect.bottom - 70, 200, 40)
        is_hovered = menu_btn.collidepoint(pygame.mouse.get_pos())
        btn_color = self.COLORS['button_hover'] if is_hovered else self.COLORS['button']

        pygame.draw.rect(surface, btn_color, menu_btn, border_radius=5)
        pygame.draw.rect(surface, self.COLORS['white'], menu_btn, 1, border_radius=5)

        btn_text = self.font_small.render("В главное меню", True, self.COLORS['white'])
        surface.blit(
            btn_text,
            (
                menu_btn.centerx - btn_text.get_width() // 2,
                menu_btn.centery - btn_text.get_height() // 2
            )
        )

        if is_hovered and random.random() < 0.3:
            shake_x = random.randint(-1, 1)
            shake_y = random.randint(-1, 1)
            menu_btn.move_ip(shake_x, shake_y)

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Обрабатывает клики мыши"""
        if not self.show_dialog:
            return False

        if self.is_show_ending:
            return self._handle_ending_click(pos)

        # Обработка кнопки "Назад"
        if self.dialog_history:
            back_btn = pygame.Rect(
                self.dialog_rect.x + 10,
                self.dialog_rect.y + self.dialog_rect.height - 30,
                60,
                20
            )
            if back_btn.collidepoint(pos):
                self.previous()
                return True

        # Обработка выбора
        if self.waiting_for_choice and hasattr(self, 'choice_buttons'):
            for i, btn_rect in enumerate(self.choice_buttons):
                if btn_rect.collidepoint(pos):
                    choice = self.choices[i]
                    self._handle_choice_effects(choice)

                    next_step = choice.get("next_scene", choice.get("next"))
                    if next_step:
                        if "next_scene" in choice:
                            self.start_scene(next_step)
                        else:
                            self.start_dialog(next_step)
                    else:
                        self.next()
                    return True

        # Обработка клика по диалоговому окну
        if self.dialog_rect.collidepoint(pos):
            self.next()
            return True

        return False

    def _handle_choice_effects(self, choice: Dict) -> None:
        """Обрабатывает эффекты выбора"""
        self.choice_result = choice.get("next")
        self.waiting_for_choice = False
        self.choices = []
        self.choice_buttons = []

        if "conditions" in choice:
            stats = self.save_system.get_character_stats()
            for stat, min_value in choice["conditions"].items():
                if stats.get(stat, 0) < min_value:
                    return

        if "change_stats" in choice:
            for stat, change in choice["change_stats"].items():
                self.save_system.update_character_stat(stat, change)

        if "remove_item" in choice:
            self.save_system.remove_from_inventory(choice["remove_item"])

        if "add_item" in choice:
            self.save_system.add_to_inventory(choice["add_item"])

        if "unlock_action" in choice:
            self.save_system.unlock_action(choice["unlock_action"])

        if "set_flag" in choice:
            flag, value = choice["set_flag"]
            self.save_system.set_story_flag(flag, value)

        if "next_scene" in choice:
            self.start_scene(choice["next_scene"])

    def _handle_ending_click(self, pos: Tuple[int, int]) -> bool:
        """Обрабатывает клики на экране концовки"""
        menu_btn = pygame.Rect(800 // 2 - 100, 600 // 2 + 80, 200, 40)
        if menu_btn.collidepoint(pos):
            self.is_show_ending = False
            return True
        return False

    def start_scene(self, scene_id: str) -> None:
        """Начинает новую сцену"""
        if scene_id in self.dialogs:
            self.current_dialog = self.dialogs[scene_id]["ru"].copy()
            self.next()
        else:
            print(f"Scene {scene_id} not found!")

    def show_ending(self, ending_title: str) -> None:
        """Показывает экран концовки"""
        self.is_show_ending = True
        self.current_ending = ending_title
        self.show_dialog = False

