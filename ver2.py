from pathlib import Path

import pygame
import sys
import random
import math
import json
import os
from typing import List, Dict, Optional, Tuple, Union, Set, Any
from enum import Enum

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 800, 600
BLUE_DARK = (5, 5, 30)
BLUE_LIGHT = (10, 10, 50)
WHITE = (223, 223, 223)  # Не чисто белый для ретро-эффекта
YELLOW = (255, 255, 0)
BUTTON_COLOR = (50, 50, 150)
BUTTON_HOVER = (70, 70, 200)
DIALOG_BG = (20, 20, 50, 220)  # Полупрозрачный фон диалогов
CHOICE_BG = (30, 30, 70, 240)  # Полупрозрачный фон выбора
BLACK = (0, 0, 0)


class GameState(Enum):
    MENU = 0
    PLAY = 1
    ZOOM = 2
    ENDING = 3

class Locale:
    def __init__(self, file_path: str = 'locales.json'):
        self.translations: Dict[str, Any] = {}
        self.current_lang = "ru"  # Текущий язык по умолчанию
        self.load_translations(Path(__file__).parent / file_path)

    def load_translations(self, file_path: Path) -> None:
        """Загружает переводы из JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading translations: {e}")
            self.translations = {}

    def get(self, key: str) -> str:
        """
        Получает перевод по ключу для текущего языка
        :param key: Ключ перевода в формате 'category.subkey'
        :return: Найденный перевод или ключ в квадратных скобках, если не найден
        """
        if not self.translations:
            return f"[{key}]"

        keys = key.split('.')
        result = self.translations.get(self.current_lang, {})

        for k in keys:
            if not isinstance(result, dict):
                break
            result = result.get(k, {})

        if not result or isinstance(result, dict):
            return f"[{key}]"

        return result

    @property
    def language(self):
        return self.current_lang

    @language.setter
    def language(self, lang: str):
        """Устанавливает текущий язык"""
        if lang in self.translations:
            self.current_lang = lang

class Starfield:
    def __init__(self, width, height, star_count=200):
        self.width = width
        self.height = height
        self.stars = []

        # Создаем звезды
        for _ in range(star_count):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 3)
            speed = random.uniform(0.1, 0.5)
            self.stars.append([x, y, size, speed])

    def update(self, zoom_factor=1.0):
        """Обновление позиций звезд"""
        for star in self.stars:
            star[1] += star[3] * (zoom_factor ** 0.5)
            if star[1] > self.height:
                star[1] = 0
                star[0] = random.randint(0, self.width)

    def draw(self, screen, current_state, zoom_factor=1.0, target_star=None):
        """Отрисовка звездного поля"""
        if current_state == GameState.ZOOM and target_star:
            # Режим с увеличением (зум)
            for star in self.stars:
                x = (star[0] - target_star[0]) * zoom_factor + target_star[0]
                y = (star[1] - target_star[1]) * zoom_factor + target_star[1]
                size = star[2] * zoom_factor

                if -size < x < self.width + size and -size < y < self.height + size:
                    pygame.draw.circle(screen, WHITE, (int(x), int(y)), int(size))
        else:
            # Обычный режим
            for star in self.stars:
                pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[2])

class Background:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.starfield = Starfield(width, height)
        self.particles = []
        self.shake_offset = [0, 0]
        self.shake_intensity = 0
        self.shake_duration = 0

    def update(self, zoom_factor=1.0, target_star=None):
        self.starfield.update(zoom_factor)

        # Обновляем частицы
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)

        # Обновляем эффект дрожания
        if self.shake_duration > 0:
            self.shake_offset[0] = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_offset[1] = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_duration -= 1
        else:
            self.shake_offset = [0, 0]

    def draw(self, screen, current_state, zoom_factor=1.0, target_star=None):
        screen.fill(BLUE_DARK)
        # Рисуем звездное поле только если не в игровом режиме
        self.starfield.draw(screen, current_state, zoom_factor, target_star)

        # Рисуем частицы (если есть)
        for p in self.particles:
            pygame.draw.circle(screen, WHITE, (int(p[0]), int(p[1])), p[4])

    def add_particles(self, x, y, count=20):
        for _ in range(count):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(1, 5)
            self.particles.append([
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.randint(1, 3),
                random.randint(10, 30)  # Время жизни
            ])

    def start_shake(self, intensity=3, duration=10):
        self.shake_intensity = intensity
        self.shake_duration = duration

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.original_rect = pygame.Rect(x, y, width, height)
        self.rect = self.original_rect.copy()
        self.text = text
        self.action = action
        self.is_hovered = False
        self.current_size = 16
        self.target_size = 16
        self.glow = 0

        # Космические текстуры для кнопок
        self.normal_surface = self.create_cosmic_surface(width, height, False)
        self.hover_surface = self.create_cosmic_surface(width, height, True)

    def create_cosmic_surface(self, width, height, glowing):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        color1 = (50, 50, 150, 200) if not glowing else (70, 70, 200, 250)
        color2 = (100, 100, 255, 50) if not glowing else (150, 150, 255, 100)

        # Основной цвет
        pygame.draw.rect(surface, color1, (0, 0, width, height), border_radius=10)

        # Космические эффекты
        for _ in range(20):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 2)
            pygame.draw.circle(surface, color2, (x, y), size)

        # Обводка
        pygame.draw.rect(surface, WHITE, (0, 0, width, height), 2, border_radius=10)
        return surface

    def draw(self, surface):
        # Плавные анимации
        self.current_size += (self.target_size - self.current_size) * 0.2
        self.glow += (int(self.is_hovered) * 10 - self.glow) * 0.1

        # Рисуем космическую кнопку
        current_surface = self.hover_surface if self.is_hovered else self.normal_surface
        surface.blit(current_surface, self.rect)

        # Текст с анимацией
        font = pixel_font_small
        if self.is_hovered:
            font = pygame.font.SysFont("Courier New", 18, bold=True)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)  # Проверяем текущий rect, а не original_rect
        if self.is_hovered:
            self.rect = self.original_rect.move(
                random.randint(-1, 1),
                random.randint(-1, 1)
            )
        else:
            self.rect = self.original_rect.copy()
        self.target_size = 18 if self.is_hovered else 16
        return self.is_hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.action:
                self.action()

class GameSettings:
    """Класс для хранения настроек игры"""

    def __init__(self):
        self._settings = {
            "music_volume": 0.5,
            "fullscreen": False,
            "language": "ru"
        }
        self.settings_file = "game_settings.json"
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                loaded_settings = json.load(f)
                self._settings.update(loaded_settings)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self._settings, f)

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value

    @property
    def music_volume(self):
        return self._settings.get("music_volume", 0.5)

    @music_volume.setter
    def music_volume(self, value):
        self._settings["music_volume"] = max(0.0, min(1.0, value))

    @property
    def fullscreen(self):
        return self._settings.get("fullscreen", False)

    @fullscreen.setter
    def fullscreen(self, value):
        self._settings["fullscreen"] = bool(value)

    @property
    def language(self):
        return self._settings.get("language", "ru")

    @language.setter
    def language(self, value):
        if value in ["ru", "en"]:
            self._settings["language"] = value

class MusicPlayer:
    def __init__(self, settings: GameSettings, music_folder="music"):
        self.music_folder = music_folder
        self.playlist = []
        self.current_track_index = 0
        self.setting = settings
        self.volume = settings.music_volume
        self.load_playlist()

        # Инициализация микшера pygame, если еще не инициализирован
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def load_playlist(self):
        """Загружает все поддерживаемые аудиофайлы из указанной папки"""
        supported_formats = ['.mp3', '.ogg', '.wav']

        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            #сделать доп окном
            print(f"Папка {self.music_folder} создана. Добавьте в нее музыку.")
            return

        for file in os.listdir(self.music_folder):
            if any(file.lower().endswith(ext) for ext in supported_formats):
                self.playlist.append(os.path.join(self.music_folder, file))

        if not self.playlist:
            print(f"В папке {self.music_folder} не найдено поддерживаемых аудиофайлов.")
        else:
            print(f"Загружено {len(self.playlist)} треков в плейлист.")

    def play(self, shuffle=False):
        """Начинает воспроизведение плейлиста"""
        if not self.playlist:
            print("Нет треков для воспроизведения.")
            return

        if shuffle:
            random.shuffle(self.playlist)
            self.current_track_index = 0

        self._play_current_track()

    def _play_current_track(self):
        """Воспроизводит текущий трек"""
        if not self.playlist:
            return

        pygame.mixer.music.load(self.playlist[self.current_track_index])
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play()

        # Устанавливаем обработчик события окончания трека
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        #в настройки добавить
        print(f"Сейчас играет: {os.path.basename(self.playlist[self.current_track_index])}")

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
        pygame.mixer.music.pause()

    def unpause(self):
        """Возобновляет воспроизведение"""
        pygame.mixer.music.unpause()

    def update(self, events):
        """Обрабатывает события окончания трека"""
        for event in events:
            if event.type == pygame.USEREVENT and event.type == pygame.mixer.music.get_endevent():
                self.next_track()

class Menu:
    def __init__(self, width, height,current_state, settings: GameSettings):
        self.width = width
        self.height = height
        self.background = Background(width, height)
        self.locale = Locale()
        self.game_settings = settings  # Хранит настройки
        self.settings = SettingsManager(self.game_settings)

        # Инициализация кнопок с локализацией
        self.buttons = [
            Button(width // 2 - 100, height // 2 - 60, 200, 50,
                   self.locale.get("menu.play"), self.play_action),
            Button(width // 2 - 100, height // 2 + 10, 200, 50,
                   self.locale.get("menu.settings"), self.show_settings),
            Button(width // 2 - 100, height // 2 + 80, 200, 50,
                   self.locale.get("menu.quit"), self.quit_action)
        ]

        self.show_settings_menu = False
        self.current_state = current_state
        self.zoom_factor = 10.0
        self.max_zoom = 20.0
        self.zoom_speed = 0.1
        self.target_star = [width // 2, height // 2]

        self.zoom_darkness = 0
        self.show_black_screen = False

    def update_buttons_text(self):
        """Обновляет текст кнопок при изменении языка"""
        self.buttons[0].text = self.locale.get("menu.play")
        self.buttons[1].text = self.locale.get("menu.settings")
        self.buttons[2].text = self.locale.get("menu.quit")

    def play_action(self):
        self.current_state = GameState.ZOOM # Добавлено
        self.zoom_factor = 1.0
        self.target_star = random.choice(self.background.starfield.stars)[:2]
        self.background.add_particles(self.target_star[0], self.target_star[1])
        self.background.start_shake(5, 15)

    def update(self):
        self.background.update(self.zoom_factor, self.target_star if self.current_state == GameState.ZOOM else None)
        self.zoom_darkness = min(255, int(255 * (self.zoom_factor / self.max_zoom)))

        if self.current_state == GameState.ZOOM:
            self.zoom_factor += self.zoom_speed
            if self.zoom_factor >= self.max_zoom:
                self.current_state = GameState.PLAY
                print(f"Зум завершен. Текущий статус игры: {self.current_state}")  # Добавлено
                self.zoom_factor = 1.0
                # После завершения зума устанавливаем флаг для черного экрана
                self.show_black_screen = True

    def show_settings(self):
        self.show_settings_menu = True
        self.background.start_shake(3, 10)

    def quit_action(self):
        pygame.quit()
        sys.exit()

    def draw(self, screen, current_state):
        # Рисуем фон
        screen.fill(BLUE_DARK)
        if current_state == GameState.MENU or current_state== GameState.ZOOM:
            self.background.draw(screen, self.current_state, self.zoom_factor, self.target_star)
            self.background.starfield.draw(screen, self.current_state, self.zoom_factor, self.target_star)

        # Добавляем затемнение во время зума
        if self.current_state == GameState.ZOOM and self.zoom_darkness > 0:
            dark_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            dark_surface.fill((0, 0, 0, self.zoom_darkness))
            screen.blit(dark_surface, (0, 0))

        if self.show_settings_menu:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Полупрозрачный черный
            screen.blit(overlay, (0, 0))

        if self.current_state == GameState.MENU:
            # Рисуем заголовок с мерцанием
            if self.show_settings_menu == False:
                title_color = (255, 255, 255) if pygame.time.get_ticks() % 1000 < 500 else (100, 100, 255)
                title = pixel_font_large.render(self.locale.get("ui.title"), True, title_color)
                screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))

            # Рисуем кнопки
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.check_hover(mouse_pos)
                button.draw(screen)

            # Рисуем текст автора
            author_text = pixel_font_small.render("tg: @bebrita", True, WHITE)
            screen.blit(author_text, (WIDTH // 2 - 60, self.height - 460))

            # Если нужно показать меню настроек
            if self.show_settings_menu:
                self.settings.draw(screen, WIDTH, HEIGHT, pixel_font_large, pixel_font_small, WHITE, BUTTON_COLOR,
                                   BUTTON_HOVER)

    def change_language(self, lang: str):
        """Изменяет язык интерфейса"""
        if lang in self.locale.translations:
            self.settings.language = lang
            self.locale.language = lang  # Обновляем язык в локалях
            self.update_buttons_text()

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:
                self.quit_action()

            # Если открыты настройки - обрабатываем только их
            if self.show_settings_menu:
                result = self.settings.handle_event(event)
                if result == "close":
                    self.show_settings_menu = False
                elif result == "toggle_fullscreen":
                    # Обработка переключения полноэкранного режима
                    if self.settings.settings.fullscreen:
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        pygame.display.set_mode((WIDTH, HEIGHT))
                continue  # Пропускаем обработку других событий

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    button.handle_event(event)

    def check_hover(self, pos):
        self.settings.check_hover(pos)

class SettingsManager:
    """Класс для управления отображением настроек"""

    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.locale = Locale()

        # Инициализация всех элементов интерфейса
        self.sett_rect = pygame.Rect(0, 0, 400, 400)
        self.sett_close_btn = pygame.Rect(0, 0, 30, 30)
        self.music_down_btn = pygame.Rect(0, 0, 30, 25)
        self.music_up_btn = pygame.Rect(0, 0, 30, 25)
        self.fullscreen_btn = pygame.Rect(0, 0, 80, 25)
        self.language_btn = pygame.Rect(0, 0, 80, 25)
        self.save_btn = pygame.Rect(0, 0, 100, 30)
        self.shuffle_btn = pygame.Rect(0, 0, 40, 40)
        self.prev_btn = pygame.Rect(0, 0, 40, 40)
        self.play_btn = pygame.Rect(0, 0, 40, 40)
        self.next_btn = pygame.Rect(0, 0, 40, 40)

        # Состояния наведения
        self.music_down_hovered = False
        self.music_up_hovered = False
        self.fullscreen_hovered = False
        self.language_hovered = False
        self.save_hovered = False
        self.close_hovered = False
        self.shuffle_hovered = False
        self.prev_hovered = False
        self.play_hovered = False
        self.next_hovered = False

        self.track_text_offset = 0
        self.track_text_width = 0
        self.last_text_update = 0

    def draw(self, surface, WIDTH, HEIGHT, pixel_font_large, pixel_font_small, WHITE, BUTTON_COLOR, BUTTON_HOVER):
        # Обновляем координаты основного прямоугольника
        self.sett_rect.update(WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400)

        # Рисуем основное окно настроек
        pygame.draw.rect(surface, (20, 20, 50), self.sett_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.sett_rect, 2, border_radius=10)

        # Заголовок
        title = pixel_font_large.render(self.locale.get("menu.settings"), True, WHITE)
        surface.blit(title, (self.sett_rect.centerx - title.get_width() // 2, self.sett_rect.y + 20))

        # Обновляем и рисуем кнопку закрытия
        self.sett_close_btn.update(self.sett_rect.right - 40, self.sett_rect.y + 10, 30, 30)
        pygame.draw.rect(surface, (200, 50, 50) if not self.close_hovered else (230, 80, 80),
                         self.sett_close_btn, border_radius=15)
        close_text = pixel_font_small.render("X", True, WHITE)
        surface.blit(close_text, (self.sett_close_btn.centerx - close_text.get_width() // 2,
                                  self.sett_close_btn.centery - close_text.get_height() // 2))

        # Отрисовка настроек
        y_offset = self.sett_rect.y + 70

        # Громкость музыки
        music_vol = self.settings.get("music_volume", 0.5)
        text = pixel_font_small.render(f"{self.locale.get("settings.music_volume")}: {int(music_vol * 100)}%", True, WHITE)
        surface.blit(text, (self.sett_rect.x + 25, y_offset))

        # Обновляем и рисуем кнопки регулировки музыки
        self.music_down_btn.update(self.sett_rect.x + 280, y_offset, 30, 25)
        self.music_up_btn.update(self.sett_rect.x + 340, y_offset, 30, 25)

        pygame.draw.rect(surface, BUTTON_HOVER if self.music_down_hovered else BUTTON_COLOR,
                         self.music_down_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.music_down_btn, 1, border_radius=5)
        text = pixel_font_small.render("-", True, WHITE)
        surface.blit(text, (self.music_down_btn.centerx - text.get_width() // 2,
                            self.music_down_btn.centery - text.get_height() // 2))

        pygame.draw.rect(surface, BUTTON_HOVER if self.music_up_hovered else BUTTON_COLOR,
                         self.music_up_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.music_up_btn, 1, border_radius=5)
        text = pixel_font_small.render("+", True, WHITE)
        surface.blit(text, (self.music_up_btn.centerx - text.get_width() // 2,
                            self.music_up_btn.centery - text.get_height() // 2))

        # Добавляем музыкальный плеер после настроек громкости

        y_offset += 40

        # Размеры и отступы
        btn_size = 40
        spacing = 25
        start_x = self.sett_rect.x + 90

        # 1. Кнопка перемешать
        self.shuffle_btn = pygame.Rect(start_x, y_offset, btn_size, btn_size)
        pygame.draw.rect(surface, BUTTON_HOVER if self.shuffle_hovered else BUTTON_COLOR,
                         self.shuffle_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.shuffle_btn, 1, border_radius=5)
        # Иконка перемешивания (две изогнутые стрелки)
        pygame.draw.line(surface, WHITE,
                         (self.shuffle_btn.x + 30, self.shuffle_btn.y + 20),
                         (self.shuffle_btn.x + 5, self.shuffle_btn.y + 20), 2)
        pygame.draw.polygon(surface, WHITE, [
            (self.shuffle_btn.x + 5, self.shuffle_btn.y + 20),
            (self.shuffle_btn.x + 10, self.shuffle_btn.y + 15),
            (self.shuffle_btn.x + 10, self.shuffle_btn.y + 25)
        ])

        # Правая стрелка
        pygame.draw.line(surface, WHITE,
                         (self.shuffle_btn.x + 25, self.shuffle_btn.y + 20),
                         (self.shuffle_btn.x + 30, self.shuffle_btn.y + 20), 2)
        pygame.draw.polygon(surface, WHITE, [
            (self.shuffle_btn.x + 35, self.shuffle_btn.y + 20),
            (self.shuffle_btn.x + 30, self.shuffle_btn.y + 15),
            (self.shuffle_btn.x + 30, self.shuffle_btn.y + 25)
        ])

        # 2. Кнопка предыдущий трек
        self.prev_btn = pygame.Rect(start_x + btn_size + spacing, y_offset, btn_size, btn_size)
        pygame.draw.rect(surface, BUTTON_HOVER if self.prev_hovered else BUTTON_COLOR,
                         self.prev_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.prev_btn, 1, border_radius=5)
        # Иконка "предыдущий трек" (две палочки и треугольник)
        pygame.draw.rect(surface, WHITE, (self.prev_btn.x + 22, self.prev_btn.y + 12, 3, 18))
        pygame.draw.rect(surface, WHITE, (self.prev_btn.x + 28, self.prev_btn.y + 12, 3, 18))
        pygame.draw.polygon(surface, WHITE, [
            (self.prev_btn.x + 7, self.prev_btn.y + 20),
            (self.prev_btn.x + 17, self.prev_btn.y + 12),
            (self.prev_btn.x + 17, self.prev_btn.y + 28)
        ])

        # 3. Кнопка play/pause
        is_playing = pygame.mixer.music.get_busy()
        self.play_btn = pygame.Rect(start_x + 2 * (btn_size + spacing), y_offset, btn_size, btn_size)
        pygame.draw.rect(surface, BUTTON_HOVER if self.play_hovered else BUTTON_COLOR,
                         self.play_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.play_btn, 1, border_radius=5)

        if is_playing:
            # Иконка паузы (две вертикальные линии)
            pygame.draw.rect(surface, WHITE, (self.play_btn.x + 13, self.play_btn.y + 12, 5, 18))
            pygame.draw.rect(surface, WHITE, (self.play_btn.x + 23, self.play_btn.y + 12, 5, 18))
        else:
            # Иконка play (треугольник)
            pygame.draw.polygon(surface, WHITE, [
                (self.play_btn.x + 10, self.play_btn.y + 10),
                (self.play_btn.x + 10, self.play_btn.y + 30),
                (self.play_btn.x + 30, self.play_btn.y + 20)
            ])

        # 4. Кнопка следующий трек
        self.next_btn = pygame.Rect(start_x + 3 * (btn_size + spacing), y_offset, btn_size, btn_size)
        pygame.draw.rect(surface, BUTTON_HOVER if self.next_hovered else BUTTON_COLOR,
                         self.next_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.next_btn, 1, border_radius=5)
        # Иконка "следующий трек" (две палочки и треугольник)
        pygame.draw.rect(surface, WHITE, (self.next_btn.x + 8, self.next_btn.y + 12, 3, 18))
        pygame.draw.rect(surface, WHITE, (self.next_btn.x + 14, self.next_btn.y + 12, 3, 18))
        pygame.draw.polygon(surface, WHITE, [
            (self.next_btn.x + 31, self.next_btn.y + 20),
            (self.next_btn.x + 21, self.next_btn.y + 12),
            (self.next_btn.x + 21, self.next_btn.y + 28)
        ])

        # Название текущего трека
        if music_player.playlist:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_text_update > 50:  # Обновляем каждые 50 мс
                self.track_text_offset -= 1
                self.last_text_update = current_time

            current_track = os.path.basename(music_player.playlist[music_player.current_track_index])
            current_track = os.path.splitext(current_track)[0]

            # Создаем поверхность с текстом
            track_text = pixel_font_small.render(current_track, True, WHITE)
            self.track_text_width = track_text.get_width()

            # Размеры "ленты" для текста
            tape_width = 340  # Ширина области для текста
            tape_rect = pygame.Rect(self.sett_rect.x + 25, y_offset + 50, tape_width, 20)

            # Если текст шире ленты - делаем бегущую строку
            if self.track_text_width > tape_width:
                # Добавляем пробел между повторениями текста
                spacer_width = 60  # Фиксированная ширина пробела
                looped_text_width = self.track_text_width + spacer_width

                # Создаем поверхность с текстом + пробел + текст
                looped_text = pygame.Surface((looped_text_width * 2, 20), pygame.SRCALPHA)
                looped_text.blit(track_text, (0, 0))
                looped_text.blit(track_text, (looped_text_width, 0))

                # Сбрасываем смещение, когда весь текст прокрутился
                if self.track_text_offset < -looped_text_width:
                    self.track_text_offset = 0

                # Выводим видимую часть
                visible_part = pygame.Surface((tape_width, 20), pygame.SRCALPHA)
                visible_part.blit(looped_text, (self.track_text_offset, 0))
                surface.blit(visible_part, (tape_rect.x, tape_rect.y))

            else:
                # Если текст помещается - просто центрируем
                text_x = tape_rect.x + (tape_width - self.track_text_width) // 2
                surface.blit(track_text, (text_x, tape_rect.y))

        y_offset += 80

        # Полноэкранный режим
        fullscreen = self.settings.get("fullscreen", False)
        text = pixel_font_small.render(f"{self.locale.get("settings.fullscreen")}:", True, WHITE)
        surface.blit(text, (self.sett_rect.x + 25, y_offset))

        # Обновляем и рисуем кнопку полноэкранного режима
        self.fullscreen_btn.update(self.sett_rect.x + 285, y_offset, 80, 25)
        btn_color = (0, 200, 0) if fullscreen else (200, 0, 0)
        if self.fullscreen_hovered:
            btn_color = (0, 230, 0) if fullscreen else (230, 0, 0)
        btn_text = self.locale.get("settings.on") if fullscreen else self.locale.get("settings.off")

        pygame.draw.rect(surface, btn_color, self.fullscreen_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.fullscreen_btn, 1, border_radius=5)
        text = pixel_font_small.render(btn_text, True, WHITE)
        surface.blit(text, (self.fullscreen_btn.centerx - text.get_width() // 2,
                            self.fullscreen_btn.centery - text.get_height() // 2))

        y_offset += 40

        # Язык
        language = self.settings.get("language", "ru")
        text = pixel_font_small.render(f"{self.locale.get("settings.language")}:", True, WHITE)
        surface.blit(text, (self.sett_rect.x + 25, y_offset))

        # Обновляем и рисуем кнопку языка
        self.language_btn.update(self.sett_rect.x + 285, y_offset, 80, 25)
        pygame.draw.rect(surface, BUTTON_HOVER if self.language_hovered else BUTTON_COLOR,
                         self.language_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.language_btn, 1, border_radius=5)
        text = pixel_font_small.render(language.upper(), True, WHITE)
        surface.blit(text, (self.language_btn.centerx - text.get_width() // 2,
                            self.language_btn.centery - text.get_height() // 2))

        # Обновляем и рисуем кнопку сохранения
        y_offset += 60
        self.save_btn.update(self.sett_rect.centerx - 50, y_offset, 100, 30)
        pygame.draw.rect(surface, (0, 180, 0) if self.save_hovered else (0, 150, 0),
                         self.save_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.save_btn, 1, border_radius=5)
        text = pixel_font_small.render(f"{self.locale.get("menu.save")}", True, WHITE)
        surface.blit(text, (self.save_btn.centerx - text.get_width() // 2,
                            self.save_btn.centery - text.get_height() // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.sett_close_btn.collidepoint(event.pos):
                return "close"
            elif self.shuffle_btn.collidepoint(event.pos):
                music_player.play(shuffle=True)
            elif self.prev_btn.collidepoint(event.pos):
                music_player.prev_track()
            elif self.play_btn.collidepoint(event.pos):
                if pygame.mixer.music.get_busy():
                    music_player.pause()
                else:
                    music_player.unpause()
            elif self.next_btn.collidepoint(event.pos):
                music_player.next_track()
            elif self.music_down_btn.collidepoint(event.pos):
                self.settings.music_volume = max(0, self.settings.music_volume - 0.1)
                music_player.set_volume(self.settings.music_volume)
            elif self.music_up_btn.collidepoint(event.pos):
                self.settings.music_volume = min(1, self.settings.music_volume + 0.1)
                music_player.set_volume(self.settings.music_volume)
            elif self.fullscreen_btn.collidepoint(event.pos):
                self.settings.fullscreen = not self.settings.fullscreen
                return "toggle_fullscreen"
            elif self.language_btn.collidepoint(event.pos):
                # Изменено: теперь обновляем и настройки, и локаль
                new_lang = "en" if self.settings.language == "ru" else "ru"
                self.settings.language = new_lang
                self.locale.language = new_lang  # Обновляем язык в локалях
                return "language_changed"  # Можно вернуть флаг, если нужно обработать где-то ещё
            elif self.save_btn.collidepoint(event.pos):
                self.settings.save_settings()
        return None

    def check_hover(self, pos):
        self.music_down_hovered = self.music_down_btn.collidepoint(pos)
        self.shuffle_hovered = self.shuffle_btn.collidepoint(pos)
        self.prev_hovered = self.prev_btn.collidepoint(pos)
        self.play_hovered = self.play_btn.collidepoint(pos)
        self.next_hovered = self.next_btn.collidepoint(pos)
        self.music_up_hovered = self.music_up_btn.collidepoint(pos)
        self.fullscreen_hovered = self.fullscreen_btn.collidepoint(pos)
        self.language_hovered = self.language_btn.collidepoint(pos)
        self.save_hovered = self.save_btn.collidepoint(pos)
        self.close_hovered = self.sett_close_btn.collidepoint(pos)
        return None

class GameData:
    def __init__(self):
        self.character_stats = {
            "Отвага": 60,
            "ПТСР": 30,
            "Блядство": 20,
            "ЧСВ": 60
        }
        self.inventory: List[str] = []
        self.achievements: Set[str] = set()
        self.save_file = "game_save.json"

        # Загружаем сохранение при инициализации
        self.load_game()

    def load_game(self) -> bool:
        """Загружает сохранение из файла, возвращает True если успешно"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.character_stats = data.get("character_stats", self.character_stats)
                    self.inventory = data.get("inventory", [])
                    self.achievements = set(data.get("achievements", []))
                return True
            return False
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def save_game(self):
        """Сохраняет текущее состояние игры в файл"""
        data = {
            "character_stats": self.character_stats,
            "inventory": self.inventory,
            "achievements": list(self.achievements)
        }

        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_stat(self, stat_name: str, change: int):
        """Изменяет характеристику персонажа"""
        if stat_name in self.character_stats:
            self.character_stats[stat_name] = max(0, min(100, self.character_stats[stat_name] + change))
            return True
        return False

    def add_to_inventory(self, item: str):
        """Добавляет предмет в инвентарь"""
        if item not in self.inventory:
            self.inventory.append(item)
            return True
        return False

    def remove_from_inventory(self, item: str) -> bool:
        """Удаляет предмет из инвентаря"""
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    def unlock_achievement(self, achievement: str):
        """Разблокирует ачивку"""
        self.achievements.add(achievement)

    def has_achievement(self, achievement: str) -> bool:
        """Проверяет, есть ли ачивка"""
        return achievement in self.achievements


    def get_stat_color(self, stat: str) -> tuple:
        """Возвращает цвет для отображения характеристики"""
        colors = {
            "Отвага": (0, 200, 0),  # Зеленый
            "ПТСР": (200, 0, 0),  # Красный
            "Блядство": (0, 100, 200),  # Синий
            "ЧСВ": (200, 200, 0)  # Желтый
        }
        return colors.get(stat, (255, 255, 255))  # Белый по умолчанию

class GameUI:
    def __init__(self, width, height, game_data: GameData, settings: GameSettings):
        self.game_data = game_data
        self.settings = settings
        self.locale = Locale()
        self.background = Background(width, height)

        self.zoom_factor = 10.0
        self.target_star = [width // 2, height // 2]

        # UI элементы
        self.buttons = {
            "actions": pygame.Rect(60, HEIGHT - 540, 130, 30),
            "inventory": pygame.Rect(60, HEIGHT - 500, 130, 30),
            "settings": pygame.Rect(60, HEIGHT - 460, 130, 30)
        }

        self.close_buttons = {
            "actions": pygame.Rect(0, 0, 30, 30),
            "inventory": pygame.Rect(0, 0, 30, 30)
        }

        self.hover_states = {
            "actions": False,
            "inventory": False,
            "settings": False,
            "actions_close": False,
            "inventory_close": False
        }

        self.visible_panels = {
            "actions": False,
            "inventory": False,
            "settings": False
        }

        # Инициализация атрибутов для управления изображениями
        self.current_image_index = 0
        self.last_image_change = 0

        # Загрузка изображений
        self.load_images()

    def load_images(self):
        """Загружает изображения для UI"""
        self.images = {}
        try:
            # Основные изображения
            for i in range(1, 4):
                img_path = Path(__file__).parent / f"pics/image{i}.jpg"
                if img_path.exists():
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    img = pygame.transform.scale(img, (500, 500))
                    self.images[f"main_{i}"] = img

            # Специальные изображения
            special_images = {
                4: "timeout",
                5: "hover"
            }

            for num, name in special_images.items():
                img_path = Path(__file__).parent / f"pics/image{num}.jpg"
                if img_path.exists():
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    img = pygame.transform.scale(img, (500, 500))
                    self.images[name] = img

        except Exception as e:
            print(f"Ошибка загрузки изображений: {e}")
            # Создаем заглушки для отсутствующих изображений
            for i in range(1, 4):
                surf = pygame.Surface((500, 500), pygame.SRCALPHA)
                pygame.draw.rect(surf, (50, 50, 100, 200), (0, 0, 500, 500))
                text = pixel_font_large.render(f"Image {i}", True, WHITE)
                surf.blit(text, (250 - text.get_width() // 2, 250 - text.get_height() // 2))
                self.images[f"main_{i}"] = surf

            for name in ["timeout", "hover"]:
                surf = pygame.Surface((500, 500), pygame.SRCALPHA)
                pygame.draw.rect(surf, (100, 50, 50, 200), (0, 0, 500, 500))
                text = pixel_font_large.render(f"Special {name}", True, WHITE)
                surf.blit(text, (250 - text.get_width() // 2, 250 - text.get_height() // 2))
                self.images[name] = surf

    def draw(self, surface, current_state):
        """Отрисовывает весь UI"""

        surface.fill(BLUE_DARK)
        self.background.draw(surface, current_state, self.zoom_factor, self.target_star)
        self.background.starfield.draw(surface, current_state, self.zoom_factor, self.target_star)
        self.background.starfield.update()

        # Фон с затемнением
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        surface.blit(s, (0, 0))

        # Панель характеристик
        self.draw_stats_panel(surface)

        # Панель действий
        self.draw_actions_panel(surface)

        # Центральное изображение
        self.draw_central_image(surface)

        # Отрисовка открытых панелей
        if self.visible_panels["actions"]:
            self.draw_actions_window(surface)
        if self.visible_panels["inventory"]:
            self.draw_inventory_window(surface)
            if self.visible_panels["settings"]:
                self.draw_settings_window(surface)

    def draw_stats_panel(self, surface):
        """Отрисовывает панель характеристик"""
        panel_rect = pygame.Rect(WIDTH - 230, 50, 200, HEIGHT - 300)
        pygame.draw.rect(surface, (30, 30, 60), panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)

        title = pixel_font_small.render(self.locale.get("ui.stats_title"), True, WHITE)
        surface.blit(title, (panel_rect.x + 10, panel_rect.y + 10))

        y_offset = 50
        for stat, value in self.game_data.character_stats.items():
            # Название характеристики
            stat_text = pixel_font_small.render(stat, True, WHITE)
            surface.blit(stat_text, (panel_rect.x + 15, panel_rect.y + y_offset))

            # Полоска значения
            bar_width = 170
            filled_width = (value / 100) * bar_width
            pygame.draw.rect(surface, (50, 50, 80),
                             (panel_rect.x + 15, panel_rect.y + y_offset + 25, bar_width, 15))
            pygame.draw.rect(surface, self.game_data.get_stat_color(stat),
                             (panel_rect.x + 15, panel_rect.y + y_offset + 25, filled_width, 15))

            # Числовое значение
            value_text = pixel_font_small.render(f"{value}%", True, WHITE)
            surface.blit(value_text,
                         (panel_rect.x + bar_width - value_text.get_width() + 15,
                          panel_rect.y + y_offset + 25))

            y_offset += 50

    def draw_actions_panel(self, surface):
        """Отрисовывает панель с кнопками действий"""
        panel_rect = pygame.Rect(50, 50, 150, HEIGHT - 470)
        pygame.draw.rect(surface, (30, 30, 60), panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)

        # Кнопки
        for btn_name, rect in self.buttons.items():
            btn_color = BUTTON_HOVER if self.hover_states[btn_name] else BUTTON_COLOR
            pygame.draw.rect(surface, btn_color, rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, rect, 1, border_radius=5)

            text = pixel_font_small.render(self.locale.get(f"ui.{btn_name}"), True, WHITE)
            surface.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))

    def draw_central_image(self, surface):
        # Загрузка изображений
        if not hasattr(self, 'central_images'):
            # Инициализация изображений
            self.central_images = []

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
                    img = pygame.Surface((500, 500), pygame.SRCALPHA)
                    pygame.draw.rect(img, (50, 50, 100, 200), (0, 0, 500, 500))
                    text = pixel_font_large.render(f"Image {i}", True, WHITE)
                    img.blit(text, (250 - text.get_width() // 2, 250 - text.get_height() // 2))
                    self.central_images.append(img)

            # Загрузка специальных изображений
            self.special_images = {}
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
                    img = pygame.Surface((500, 500), pygame.SRCALPHA)
                    pygame.draw.rect(img, (100, 50, 50, 200), (0, 0, 500, 500))
                    text = pixel_font_large.render(f"Special {i}", True, WHITE)
                    img.blit(text, (250 - text.get_width() // 2, 250 - text.get_height() // 2))
                    self.special_images[name] = img

            self.current_image_index = 0
            self.last_image_change_time = pygame.time.get_ticks()
            self.last_click_time = pygame.time.get_ticks()
            self.image_rect = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 250, 500, 500)
            self.is_hovered = False
            self.showing_special = False
            self.return_to_cycle = False  # Флаг для возврата к циклу

        current_time = pygame.time.get_ticks()

        hover_image = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 200)

        # Проверка наведения мыши (показываем special image 5)
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = hover_image.collidepoint(mouse_pos)

        if self.is_hovered and "hover" in self.special_images and not self.return_to_cycle:
            surface.blit(self.special_images["hover"], self.image_rect)
            self.showing_special = True
            return

        # Обычный цикл изображений (каждые 5 секунд)
        if current_time - self.last_image_change_time > 500 and not self.return_to_cycle:
            self.current_image_index = (self.current_image_index + 1) % len(self.central_images)
            self.last_image_change_time = current_time

        # Отрисовка текущего основного изображения
        surface.blit(self.central_images[self.current_image_index], self.image_rect)
        self.showing_special = False

    def remove_black_background(self, surface, threshold=30):
        """
        Удаляет только черный фон с изображения, делая его прозрачным
        threshold - порог для определения черного цвета (0-30)
        """
        # Создаем копию поверхности для работы
        result = surface.copy()

        # Блокируем поверхность для работы с пикселями
        result.lock()

        # Перебираем все пиксели
        for x in range(result.get_width()):
            for y in range(result.get_height()):
                # Получаем цвет пикселя
                color = result.get_at((x, y))
                # Если цвет близок к черному (R, G, B все < threshold)
                if color.r < threshold and color.g < threshold and color.b < threshold:
                    # Делаем пиксель полностью прозрачным
                    result.set_at((x, y), (0, 0, 0, 0))

        # Разблокируем поверхность
        result.unlock()

        return result

    def draw_inventory_window(self, surface):
        """Отрисовывает окно инвентаря"""
        inv_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400)
        pygame.draw.rect(surface, (20, 20, 50), inv_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, inv_rect, 2, border_radius=10)

        title = pixel_font_large.render(self.locale.get("ui.inventory"), True, WHITE)
        surface.blit(title, (inv_rect.centerx - title.get_width() // 2, inv_rect.y + 20))

        # Отрисовка предметов
        y_offset = 70
        for item in self.game_data.inventory:
            text = pixel_font_small.render(item, True, WHITE)
            surface.blit(text, (inv_rect.x + 20, inv_rect.y + y_offset))
            y_offset += 30

        # Кнопка закрытия
        self.close_buttons["inventory"].update(inv_rect.right - 40, inv_rect.y + 10, 30, 30)
        btn_color = (230, 80, 80) if self.hover_states["inventory_close"] else (200, 50, 50)
        pygame.draw.rect(surface, btn_color, self.close_buttons["inventory"], border_radius=15)
        close_text = pixel_font_small.render("X", True, WHITE)
        surface.blit(close_text, (self.close_buttons["inventory"].centerx - close_text.get_width() // 2,
                                  self.close_buttons["inventory"].centery - close_text.get_height() // 2))

    def draw_actions_window(self, surface):
        """Отрисовывает окно действий"""
        act_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400)
        pygame.draw.rect(surface, (20, 20, 50), act_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, act_rect, 2, border_radius=10)

        title = pixel_font_large.render(self.locale.get("ui.actions"), True, WHITE)
        surface.blit(title, (act_rect.centerx - title.get_width() // 2, act_rect.y + 20))

        # Здесь можно добавить отрисовку доступных действий
        # Пример:
        y_offset = 70
        actions = ["Действие 1", "Действие 2", "Действие 3"]  # Заменить на реальные действия
        for action in actions:
            action_rect = pygame.Rect(act_rect.x + 20, act_rect.y + y_offset, 360, 30)
            is_hovered = action_rect.collidepoint(pygame.mouse.get_pos())

            btn_color = BUTTON_HOVER if is_hovered else BUTTON_COLOR
            pygame.draw.rect(surface, btn_color, action_rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, action_rect, 1, border_radius=5)

            text = pixel_font_small.render(action, True, WHITE)
            surface.blit(text, (action_rect.x + 10, action_rect.y + 5))

            y_offset += 40

        # Кнопка закрытия
        self.close_buttons["actions"].update(act_rect.right - 40, act_rect.y + 10, 30, 30)
        btn_color = (230, 80, 80) if self.hover_states["actions_close"] else (200, 50, 50)
        pygame.draw.rect(surface, btn_color, self.close_buttons["actions"], border_radius=15)
        close_text = pixel_font_small.render("X", True, WHITE)
        surface.blit(close_text, (self.close_buttons["actions"].centerx - close_text.get_width() // 2,
                                  self.close_buttons["actions"].centery - close_text.get_height() // 2))

    def draw_settings_window(self, surface):
        """Отрисовывает окно настроек"""
        # Используем уже существующий SettingsManager
        self.settings.draw(surface, WIDTH, HEIGHT, pixel_font_large, pixel_font_small, WHITE, BUTTON_COLOR,
                           BUTTON_HOVER)

    def handle_click(self, pos) -> bool:
        """Обрабатывает клик мыши, возвращает True если клик был обработан"""
        # Проверка кликов по кнопкам панели действий
        for btn_name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                # Закрываем все другие панели
                for panel in self.visible_panels:
                    self.visible_panels[panel] = False

                # Открываем/закрываем выбранную панель
                self.visible_panels[btn_name] = not self.visible_panels[btn_name]
                return True

        # Проверка кликов по кнопкам закрытия
        if self.visible_panels["actions"] and self.close_buttons["actions"].collidepoint(pos):
            self.visible_panels["actions"] = False
            return True

        if self.visible_panels["inventory"] and self.close_buttons["inventory"].collidepoint(pos):
            self.visible_panels["inventory"] = False
            return True

        # Обработка кликов в окне настроек
        if self.visible_panels["settings"]:
            result = self.settings.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': pos}))
            if result == "close":
                self.visible_panels["settings"] = False
                return True
            elif result:
                return True

        return False

    def check_hover(self, pos):
        """Проверяет наведение на элементы UI"""
        # Кнопки панели действий
        for btn_name in self.buttons:
            self.hover_states[btn_name] = self.buttons[btn_name].collidepoint(pos)

        # Кнопки закрытия
        if self.visible_panels["actions"]:
            self.hover_states["actions_close"] = self.close_buttons["actions"].collidepoint(pos)

        if self.visible_panels["inventory"]:
            self.hover_states["inventory_close"] = self.close_buttons["inventory"].collidepoint(pos)

        # Элементы настроек
        if self.visible_panels["settings"]:
            self.settings.check_hover(pos)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Рой Мяустанг")
clock = pygame.time.Clock()
pixel_font_large = pygame.font.SysFont("Courier New", 36, bold=True)
pixel_font_small = pygame.font.SysFont("Courier New", 16, bold=True)

current_state = GameState.MENU
settings = GameSettings()
menu = Menu(WIDTH, HEIGHT,current_state, settings)
music_player = MusicPlayer(settings,"music")
music_player.play()

game_data = GameData()
game_ui = GameUI(WIDTH, HEIGHT,game_data, settings)

running = True
while running:
    # Получаем события
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()

    # Обновляем текущее состояние игры из меню
    current_state = menu.current_state

    # Обработка событий для текущего состояния
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        # Обрабатываем клики в зависимости от состояния
        if event.type == pygame.MOUSEBUTTONDOWN:
            if current_state == GameState.PLAY:
                game_ui.handle_click(event.pos)
            elif current_state == GameState.MENU:
                menu.handle_events([event])  # Передаем событие как список

    # Обновление игровых объектов
    music_player.update(events)

    # Проверка наведения для UI
    if current_state == GameState.PLAY:
        game_ui.check_hover(mouse_pos)
    elif current_state == GameState.MENU:
        menu.check_hover(mouse_pos)
        # Рисуем игровой UI только в режиме игры

    if current_state == GameState.PLAY:
        game_ui.background.starfield.update()
        game_ui.draw(screen, current_state)

    # Всегда рисуем меню (оно само решает что рисовать в зависимости от состояния)
    if current_state == GameState.MENU or current_state==GameState.ZOOM:
        menu.draw(screen, current_state)
        menu.update()


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()