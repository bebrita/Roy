import pygame
import sys
import random
import math
import json
import os
from typing import List, Dict, Optional, Tuple, Union, Set

# консты
WIDTH, HEIGHT = 800, 600
BLUE_DARK = (5, 5, 30)
BLUE_LIGHT = (10, 10, 50)
WHITE = (223, 223, 223)  # Не чисто белый для ретро-эффекта
YELLOW = (255, 255, 0)
BUTTON_COLOR = (50, 50, 150)
BUTTON_HOVER = (70, 70, 200)
DIALOG_BG = (20, 20, 50, 220)  # Полупрозрачный фон диалогов
CHOICE_BG = (30, 30, 70, 240)  # Полупрозрачный фон выбора


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
            font =  pygame.font.SysFont("Courier New", 18, bold=True)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.original_rect.collidepoint(pos)

        if show_main_settings:
            self.is_hovered = False
            return False

        self.rect = self.original_rect.move(
            random.randint(-1, 1) * int(self.is_hovered),
            random.randint(-1, 1) * int(self.is_hovered)
        )
        self.target_size = 18 if self.is_hovered else 16
        return self.is_hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            start_shake(5, 15)
            if self.action:
                self.action()



class DialogManager:
    def __init__(self):
        self.dialog_rect = pygame.Rect(50, HEIGHT - 150, WIDTH - 100, 140)
        self.current_dialog = []
        self.current_text = ""
        self.char_index = 0
        self.text_speed = 1  # Символов за кадр
        self.last_update = 0
        self.update_delay = 30  # мс между обновлениями текста

        self.question = None
        self.choices = []
        self.choice_rects = []
        self.choice_result = None
        self.waiting_for_choice = False

        self.speaker = None
        self.speaker_image = None
        self.show_dialog = True  # Всегда показываем диалоговое окно

        self.scrolling_texts = {}  # Для хранения состояния прокрутки текста в вариантах выбора
        self.scroll_pos = 0  # Позиция прокрутки для длинных текстов
        self.scroll_speed = 2  # Скорость прокрутки
        self.last_scroll_time = 0  # Время последней прокрутки

        # Загрузка диалогов из файла
        self.dialogs = self.load_dialogs()

        self.is_show_ending = False  # было self.show_ending
        self.current_ending = None

        self.dialog_history = []

    def load_dialogs(self) -> Dict:
        try:
            print(1)
            with open('story.json', 'r', encoding='utf-8') as f:
                print(1)
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(FileNotFoundError, json.JSONDecodeError)
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
                },
                "explore": {
                    "ru": [
                        {"text": "Ты решил исследовать окрестности...", "speaker": "npc1"},
                        {"text": "Впереди тебя ждут приключения!", "speaker": "npc1"}
                    ],
                    "en": [
                        {"text": "You decided to explore the area...", "speaker": "npc1"},
                        {"text": "Adventures await you ahead!", "speaker": "npc1"}
                    ]
                }
            }

    def start_dialog(self, dialog_id: str, language: str = "ru"):
        self.dialog_history = []
        if dialog_id in self.dialogs and language in self.dialogs[dialog_id]:
            # Обрабатываем add_items отдельно
            dialog_data = self.dialogs[dialog_id][language]
            if len(dialog_data) > 0 and "add_items" in dialog_data[0]:
                for item in dialog_data[0]["add_items"]:
                    game_ui.save_system.add_to_inventory(item)
                # Пропускаем элемент с add_items
                self.current_dialog = dialog_data[1:].copy()
            else:
                self.current_dialog = dialog_data.copy()

            self.next()
        else:
            print(f"Dialog {dialog_id} not found for language {language}")

    def update(self):
        current_time = pygame.time.get_ticks()
        if (self.current_text and
                self.char_index < len(self.current_text) and
                current_time - self.last_update > self.update_delay):

            self.char_index += self.text_speed
            if self.char_index > len(self.current_text):
                self.char_index = len(self.current_text)
            self.last_update = current_time

    def next(self):
     # Не переходим дальше, пока не сделан выбор
        if self.char_index < len(self.current_text):
                self.char_index = len(self.current_text)
                return
        if self.waiting_for_choice:
            return
        if self.current_dialog:
            # Если текст еще не весь показан, показываем сразу весь

            # Берем следующую реплику
            dialog = self.current_dialog.pop(0)

            # Пропускаем элементы без текста (например, add_items)
            while "text" not in dialog and self.current_dialog:
                dialog = self.current_dialog.pop(0)

            # Проверяем, что нашли диалог с текстом
            if "text" not in dialog:
                self.current_text = ""
                return

            self.current_text = dialog["text"]
            self.char_index = 0
            self.last_update = pygame.time.get_ticks()

            # Устанавливаем говорящего
            self.speaker = dialog.get("speaker")

            if "ending" in dialog:
                self.show_ending(dialog["ending"])
                return

            # Обрабатываем эффекты для обычного текста (не только для выбора)
            if "change_stats" in dialog:
                for stat, change in dialog["change_stats"].items():
                    game_ui.save_system.update_character_stat(stat, change)
            if "add_item" in dialog:
                game_ui.save_system.add_to_inventory(dialog["add_item"])
            if "remove_item" in dialog:
                game_ui.save_system.remove_from_inventory(dialog["remove_item"])
            if "unlock_action" in dialog:
                game_ui.save_system.unlock_action(dialog["unlock_action"])
            if "set_flag" in dialog:
                flag, value = dialog["set_flag"]
                game_ui.save_system.set_story_flag(flag, value)

            # Если есть выбор, устанавливаем его
            if "choices" in dialog:
                self.question = self.current_text
                self.choices = dialog["choices"]
                self.choice_rects = []
                self.waiting_for_choice = True

            if "next_scene" in dialog and not self.waiting_for_choice:
                self.start_scene(dialog["next_scene"])
                return
        else:
            # Диалог закончен
            self.current_text = ""
            self.question = None
            self.choices = []

    def previous(self):
        """Возвращает предыдущую реплику в диалоге"""
        if self.char_index < len(self.current_text):
            self.char_index = len(self.current_text)
            return

        if self.dialog_history and not self.waiting_for_choice:
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

    def draw(self, surface: pygame.Surface):
        if not self.show_dialog:
            return
        if self.is_show_ending:
            self.draw_ending(surface)
        else:
            # Рисуем основное диалоговое окно
            dialog_surface = pygame.Surface((self.dialog_rect.width, self.dialog_rect.height), pygame.SRCALPHA)
            dialog_surface.fill(DIALOG_BG)

            # Рисуем текст (постепенно появляющийся)
            visible_text = self.current_text[:self.char_index]

            # Разбиваем текст на строки, чтобы он помещался в окно
            lines = []
            words = visible_text.split(' ')
            current_line = ""

            for word in words:
                test_line = current_line + word + " "
                # Проверяем ширину текста
                if pixel_font_small.size(test_line)[0] < self.dialog_rect.width - 40:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word + " "

            if current_line:
                lines.append(current_line)

            # Отрисовываем строки текста
            y_offset = 20
            for line in lines:
                text_surface = pixel_font_small.render(line, True, WHITE)
                dialog_surface.blit(text_surface, (20, y_offset))
                y_offset += pixel_font_small.get_linesize()

            # Если есть говорящий, отображаем его имя
            if self.speaker:
                speaker_surface = pixel_font_small.render(self.speaker, True, YELLOW)
                dialog_surface.blit(speaker_surface, (20, 5))

            # Отрисовываем диалоговое окно на основном экране
            surface.blit(dialog_surface, self.dialog_rect)

            # Если есть выбор, отображаем его после полного появления текста
            if self.waiting_for_choice and self.char_index >= len(self.current_text):
                self.draw_choices(surface)

            if self.dialog_history:
                back_btn = pygame.Rect(self.dialog_rect.x + 10, self.dialog_rect.y + self.dialog_rect.height - 30, 60, 20)
                pygame.draw.rect(surface, BUTTON_COLOR, back_btn, border_radius=3)
                pygame.draw.rect(surface, WHITE, back_btn, 1, border_radius=3)
                back_text = pixel_font_small.render("Назад", True, WHITE)
                surface.blit(back_text, (back_btn.x + 10, back_btn.y + 5))

    def draw_choices(self, surface: pygame.Surface):
        """Отрисовывает варианты выбора с проверкой условий и эффектами при наведении"""
        if not self.choices:
            return

        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        # Получаем текущие характеристики персонажа
        stats = game_ui.save_system.get_character_stats()

        # Фильтруем choices по условиям
        available_choices = []
        for choice in self.choices:
            if "conditions" not in choice:
                available_choices.append(choice)
                continue

            conditions_met = True
            for stat, min_value in choice["conditions"].items():
                if stats.get(stat, 0) < min_value:
                    conditions_met = False
                    break

            if conditions_met:
                available_choices.append(choice)

        # Если нет доступных вариантов, просто продолжаем
        if not available_choices:
            self.waiting_for_choice = False
            return

        # Рассчитываем размер окна выбора
        choice_height = len(available_choices) * 40 + 20
        choice_x = WIDTH // 2 - 150
        choice_y = HEIGHT - 150 - choice_height - 30
        choice_width = 350
        choice_height += 20

        # Сохраняем координаты окна выбора для обработки кликов
        self.choice_window_pos = (choice_x, choice_y, choice_width, choice_height)

        # Создаем поверхность для выбора
        choice_surface = pygame.Surface((choice_width, choice_height), pygame.SRCALPHA)
        choice_surface.fill(CHOICE_BG)

        y_offset = 10
        self.choice_buttons = []

        for i, choice in enumerate(available_choices):
            btn_x = 20
            btn_y = y_offset + i * 40 + 10
            btn_width = choice_width - 40
            btn_height = 30

            # Сохраняем координаты кнопки (глобальные)
            global_btn_x = choice_x + btn_x
            global_btn_y = choice_y + btn_y
            self.choice_buttons.append((global_btn_x, global_btn_y, btn_width, btn_height))

            # Проверяем наведение мыши
            is_hovered = (global_btn_x <= mouse_pos[0] <= global_btn_x + btn_width and
                          global_btn_y <= mouse_pos[1] <= global_btn_y + btn_height)

            # Цвет кнопки зависит от наведения
            btn_color = BUTTON_HOVER if is_hovered else BUTTON_COLOR
            pygame.draw.rect(choice_surface, btn_color, (btn_x, btn_y, btn_width, btn_height), border_radius=5)
            pygame.draw.rect(choice_surface, WHITE, (btn_x, btn_y, btn_width, btn_height), 1, border_radius=5)

            # Обработка текста с бегущей строкой
            text = choice["text"]
            text_surface = pixel_font_small.render(text, True, WHITE)
            text_width = text_surface.get_width()
            max_text_width = btn_width - 20  # Максимальная ширина текста с отступами

            # Если текст не помещается - делаем бегущую строку
            if text_width > max_text_width:
                # Инициализируем состояние прокрутки для этого выбора, если его нет
                if i not in self.scrolling_texts:
                    self.scrolling_texts[i] = {
                        'offset': 0,
                        'last_update': current_time,
                        'scroll_speed': 1  # Базовая скорость
                    }

                # Увеличиваем скорость при наведении
                current_speed = 3 if is_hovered else 1

                # Обновляем смещение
                if current_time - self.scrolling_texts[i]['last_update'] > 50:
                    self.scrolling_texts[i]['offset'] -= current_speed
                    self.scrolling_texts[i]['last_update'] = current_time

                    # Сбрасываем позицию, когда текст полностью ушел
                    if self.scrolling_texts[i]['offset'] < -text_width:
                        self.scrolling_texts[i]['offset'] = max_text_width

                # Создаем поверхность для видимой части текста
                visible_text = pygame.Surface((max_text_width, text_surface.get_height()), pygame.SRCALPHA)

                # Рисуем текст с текущим смещением
                visible_text.blit(text_surface, (self.scrolling_texts[i]['offset'], 0))

                # Если текст уже уходит, добавляем его повтор справа для плавного перехода
                if self.scrolling_texts[i]['offset'] < 0:
                    visible_text.blit(text_surface, (self.scrolling_texts[i]['offset'] + text_width + 20, 0))

                # Выводим видимую часть на кнопку
                choice_surface.blit(visible_text,
                                    (btn_x + 10,
                                     btn_y + btn_height // 2 - text_surface.get_height() // 2))
            else:
                # Текст помещается - просто центрируем
                choice_surface.blit(
                    text_surface,
                    (
                        btn_x + btn_width // 2 - text_surface.get_width() // 2,
                        btn_y + btn_height // 2 - text_surface.get_height() // 2
                    )
                )

        # Отрисовываем окно выбора на основном экране
        surface.blit(choice_surface, (choice_x, choice_y))

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Обрабатывает клик мыши, возвращает True, если клик был по диалогу"""
        if not self.show_dialog:
            return False
        if self.is_show_ending:
            return self.handle_ending_click(pos)
        if self.dialog_history:
            back_btn = pygame.Rect(self.dialog_rect.x + 10, self.dialog_rect.y + self.dialog_rect.height - 30, 60, 20)
            if back_btn.collidepoint(pos):
                self.previous()
                return True
        # Проверяем клик по вариантам выбора
        if self.waiting_for_choice and hasattr(self, 'choice_buttons'):
            for i, (btn_x, btn_y, btn_width, btn_height) in enumerate(self.choice_buttons):
                if (btn_x <= pos[0] <= btn_x + btn_width and
                        btn_y <= pos[1] <= btn_y + btn_height):
                    choice = self.choices[i]

                    # Обрабатываем стандартные эффекты выбора
                    self.handle_choice_effects(choice)

                    # Определяем следующий шаг (приоритет у next_scene)
                    next_step = choice.get("next_scene", choice.get("next"))

                    # Если есть следующий шаг
                    if next_step:
                        if "next_scene" in choice:
                            # Это переход между сценами
                            self.start_scene(next_step)
                        else:
                            # Это обычный переход к следующему диалогу
                            self.start_dialog(next_step)
                    else:
                        # Если нет следующего шага, просто продолжаем
                        self.next()
                    return True

        # Проверяем клик по диалоговому окну (для продолжения)
        dialog_x, dialog_y = self.dialog_rect.topleft
        dialog_width, dialog_height = self.dialog_rect.size
        if (dialog_x <= pos[0] <= dialog_x + dialog_width and
                dialog_y <= pos[1] <= dialog_y + dialog_height):
            self.next()
            return True

        if self.dialog_history:
            back_btn = pygame.Rect(dialog_x + 10, dialog_y + self.dialog_rect.height - 30, 60, 20)
            if back_btn.collidepoint(pos):
                self.previous()
                return True
        return False

    def handle_choice_effects(self, choice):
        """Обрабатывает все эффекты выбора"""
        self.choice_result = choice.get("next")  # Для обратной совместимости
        self.waiting_for_choice = False
        self.choices = []
        self.choice_buttons = []

        if "conditions" in choice:
            stats = game_ui.save_system.get_character_stats()
            for stat, min_value in choice["conditions"].items():
                if stats.get(stat, 0) < min_value:
                    return

        # Обрабатываем эффекты выбора
        if "change_stats" in choice:
            for stat, change in choice["change_stats"].items():
                game_ui.save_system.update_character_stat(stat, change)

        if "remove_item" in choice:
            game_ui.save_system.remove_from_inventory(choice["remove_item"])

        if "add_item" in choice:
            game_ui.save_system.add_to_inventory(choice["add_item"])

        if "unlock_action" in choice:
            game_ui.save_system.unlock_action(choice["unlock_action"])

        if "set_flag" in choice:
            flag, value = choice["set_flag"]
            game_ui.save_system.set_story_flag(flag, value)

        if "next_scene" in choice:
            self.start_scene(choice["next_scene"])

    def start_scene(self, scene_id: str):
        """Загружает и начинает новую сцену"""
        if scene_id in self.dialogs:
            self.current_dialog = self.dialogs[scene_id]["ru"].copy()  # Используем текущий язык
            self.next()  # Начинаем первый диалог сцены
        else:
            print(f"Scene {scene_id} not found!")

    def handle_choice(self, choice):
        # При выборе в диалоге можем:
        # 1. Добавить предмет в инвентарь
        if choice.get("add_item"):
            game_ui.save_system.add_to_inventory(choice["add_item"])

        # 2. Разблокировать новое действие
        if choice.get("unlock_action"):
            game_ui.save_system.unlock_action(choice["unlock_action"])

        # 3. Установить флаг истории
        if choice.get("set_flag"):
            flag, value = choice["set_flag"]
            game_ui.save_system.set_story_flag(flag, value)

        # 4. Изменить характеристику персонажа
        if choice.get("change_stat"):
            stat, change = choice["change_stat"]
            game_ui.save_system.update_character_stat(stat, change)

        if "next_scene" in choice:
            self.start_scene(choice["next_scene"])
        elif "next" in choice:  # Для обратной совместимости
            self.start_dialog(choice["next"])

    def show_ending(self, ending_title: str):
        """Показывает экран концовки"""
        self.is_show_ending = True
        self.current_ending = ending_title
        self.show_dialog = False

    def draw_ending(self, surface: pygame.Surface):
        """Отрисовывает экран концовки в стиле интерфейса игры"""
        if not self.is_show_ending or not self.current_ending:
            return

        # Полупрозрачный темный фон (как в основном интерфейсе)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Аналогично другим окнам
        surface.blit(overlay, (0, 0))

        # Основное окно концовки (стиль как у других панелей)
        ending_rect = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 150, 500, 300)
        pygame.draw.rect(surface, (30, 30, 60), ending_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, ending_rect, 2, border_radius=10)

        # Заголовок "КОНЦОВКА" (стиль как в других заголовках)
        title = pixel_font_large.render("КОНЦОВКА", True, WHITE)
        surface.blit(title, (ending_rect.centerx - title.get_width() // 2, ending_rect.y + 20))

        # Название концовки (аналогично тексту в диалогах)
        ending_text = pixel_font_small.render(self.current_ending, True, WHITE)
        surface.blit(ending_text,
                     (ending_rect.centerx - ending_text.get_width() // 2,
                      ending_rect.centery - ending_text.get_height() // 2))

        # Кнопка "В главное меню" (стиль как другие кнопки)
        menu_btn = pygame.Rect(ending_rect.centerx - 100, ending_rect.bottom - 70, 200, 40)

        # Проверяем наведение (как в других кнопках)
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = menu_btn.collidepoint(mouse_pos)

        # Цвет кнопки с эффектом наведения (как в других кнопках)
        btn_color = BUTTON_HOVER if is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, menu_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, menu_btn, 1, border_radius=5)

        # Текст кнопки (стиль как в других кнопках)
        btn_text = pixel_font_small.render("В главное меню", True, WHITE)
        surface.blit(btn_text,
                     (menu_btn.centerx - btn_text.get_width() // 2,
                      menu_btn.centery - btn_text.get_height() // 2))

        # Добавляем легкое дрожание при наведении (как в других кнопках)
        if is_hovered and random.random() < 0.3:
            shake_x = random.randint(-1, 1)
            shake_y = random.randint(-1, 1)
            menu_btn.move_ip(shake_x, shake_y)

        return menu_btn

    def handle_ending_click(self, pos: Tuple[int, int]) -> bool:
        """Обрабатывает клики на экране концовки"""
        if not self.is_show_ending:
            return False

        menu_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 40)
        if menu_btn.collidepoint(pos):
            self.is_show_ending = False
            global current_state
            current_state = GameState.MENU
            return True
        return False

class GameState:
    MENU = 0
    ZOOM = 1
    PLAY = 2
    ENDING = 3

class MusicPlayer:
    def __init__(self, music_folder="music", volume=0.5):
        self.music_folder = music_folder
        self.playlist = []
        self.current_track_index = 0
        self.volume = volume
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
#сделать одни настройки
class Settings:
    def __init__(self):
        self.settings = {
            "music_volume": 0.5,
            "fullscreen": False,
            "language": "ru"
        }
        self.settings_file = "game_settings.json"
        self.load_settings()

        # Инициализация всех элементов интерфейса с нулевыми координатами
        self.sett_rect = pygame.Rect(0, 0, 400, 400)
        self.sett_close_btn = pygame.Rect(0, 0, 30, 30)
        self.music_down_btn = pygame.Rect(0, 0, 30, 25)
        self.music_up_btn = pygame.Rect(0, 0, 30, 25)
        self.fullscreen_btn = pygame.Rect(0, 0, 80, 25)
        self.language_btn = pygame.Rect(0, 0, 80, 25)
        self.save_btn = pygame.Rect(0, 0, 100, 30)

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

        self.track_text_offset = 0  # Смещение текста
        self.track_text_width = 0  # Ширина текста
        self.last_text_update = 0  # Время последнего обновления

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                loaded_settings = json.load(f)
                self.settings.update(loaded_settings)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def draw(self, surface, WIDTH, HEIGHT, pixel_font_large, pixel_font_small, WHITE, BUTTON_COLOR):
        # Обновляем координаты основного прямоугольника
        self.sett_rect.update(WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400)

        # Рисуем основное окно настроек
        pygame.draw.rect(surface, (20, 20, 50), self.sett_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.sett_rect, 2, border_radius=10)

        # Заголовок
        title = pixel_font_large.render("Настройки", True, WHITE)
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
        text = pixel_font_small.render(f"Громкость музыки: {int(music_vol * 100)}%", True, WHITE)
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
        text = pixel_font_small.render("Полноэкранный режим:", True, WHITE)
        surface.blit(text, (self.sett_rect.x + 25, y_offset))

        # Обновляем и рисуем кнопку полноэкранного режима
        self.fullscreen_btn.update(self.sett_rect.x + 285, y_offset, 80, 25)
        btn_color = (0, 200, 0) if fullscreen else (200, 0, 0)
        if self.fullscreen_hovered:
            btn_color = (0, 230, 0) if fullscreen else (230, 0, 0)
        btn_text = "Вкл" if fullscreen else "Выкл"

        pygame.draw.rect(surface, btn_color, self.fullscreen_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.fullscreen_btn, 1, border_radius=5)
        text = pixel_font_small.render(btn_text, True, WHITE)
        surface.blit(text, (self.fullscreen_btn.centerx - text.get_width() // 2,
                            self.fullscreen_btn.centery - text.get_height() // 2))

        y_offset += 40

        # Язык
        language = self.settings.get("language", "ru")
        text = pixel_font_small.render("Язык:", True, WHITE)
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
        text = pixel_font_small.render("Сохранить", True, WHITE)
        surface.blit(text, (self.save_btn.centerx - text.get_width() // 2,
                            self.save_btn.centery - text.get_height() // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.sett_close_btn.collidepoint(event.pos):
                return "close"
            elif self.shuffle_btn.collidepoint(event.pos):
                music_player.play(shuffle=True)
                return "music_shuffle"
            elif self.prev_btn.collidepoint(event.pos):
                music_player.prev_track()
                return "music_prev"
            elif self.play_btn.collidepoint(event.pos):
                if pygame.mixer.music.get_busy():
                    music_player.pause()
                    return "music_pause"
                else:
                    music_player.unpause()
                    return "music_play"
            elif self.next_btn.collidepoint(event.pos):
                music_player.next_track()
                return "music_next"
            elif self.music_down_btn.collidepoint(event.pos):
                self.settings["music_volume"] = max(0, self.settings["music_volume"] - 0.1)
                music_player.set_volume(max(0, music_player.volume - 0.1))
            elif self.music_up_btn.collidepoint(event.pos):
                self.settings["music_volume"] = min(1, self.settings["music_volume"] + 0.1)
                music_player.set_volume(min(1, music_player.volume + 0.1))

            elif self.fullscreen_btn.collidepoint(event.pos):
                self.settings["fullscreen"] = not self.settings["fullscreen"]
                return "toggle_fullscreen"
            elif self.language_btn.collidepoint(event.pos):
                self.settings["language"] = "en" if self.settings["language"] == "ru" else "ru"
            elif self.save_btn.collidepoint(event.pos):
                self.save_settings()
                return "save"
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

    def get_music_volume(self) -> float:
        """Возвращает текущую громкость музыки (0.0 - 1.0)"""
        return self.settings.get("music_volume", 0.5)

class GameUI:
    def __init__(self):
        self.character_stats = {
            "Отвага": 60,
            "ПТСР": 30,
            "Блядство": 20,
            "ЧСВ": 60
        }
        # Добавляем инициализацию кнопок здесь
        self.act_btn = pygame.Rect(60, HEIGHT - 540, 130, 30)
        self.inv_btn = pygame.Rect(60, HEIGHT - 500, 130, 30)
        self.sett_btn = pygame.Rect(60, HEIGHT - 460, 130, 30)

        self.act_close_btn = pygame.Rect(0, 0, 30, 30)  # Инициализируем с нулевыми координатами
        self.inv_close_btn = pygame.Rect(0, 0, 30, 30)  # Координаты обновятся при отрисовке

        self.show_actions = False
        self.current_dialog = "Мяу"
        self.show_inventory = False
        self.show_settings = False
        self.last_click_pos = None
        self.settings = Settings()
        self.dialog_manager = DialogManager()

        self.act_hovered = False
        self.inv_hovered = False
        self.sett_hovered = False
        self.act_close_hovered = False
        self.inv_close_hovered = False

        self.save_system = GameSaveSystem()
        self.save_system.load_game()

    def draw(self, surface):
        # Черный фон с дымкой
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        surface.blit(s, (0, 0))

        # Панель характеристик справа
        self.draw_stats_panel(surface)

        # Панель действий слева
        self.draw_actions_panel(surface)

        # Центральное изображение
        self.draw_central_image(surface)

        # Диалоговое окно (рисуется всегда)
        self.dialog_manager.draw(surface)

        # Инвентарь/настройки если открыты
        if self.show_inventory:
            self.draw_inventory(surface)
        if self.show_settings:
            self.draw_settings(surface)
        if self.show_actions:
            self.draw_actions(surface)

        if self.dialog_manager.is_show_ending:
            self.dialog_manager.draw_ending(surface)

    def draw_stats_panel(self, surface):
        panel_rect = pygame.Rect(WIDTH - 230, 50, 200, HEIGHT - 300)
        pygame.draw.rect(surface, (30, 30, 60), panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)

        title = pixel_font_small.render("Характеристики", True, WHITE)
        surface.blit(title, (panel_rect.x + 10, panel_rect.y + 10))

        y_offset = 50
        stats = game_ui.save_system.get_character_stats()  # Используем данные из системы сохранений
        for stat, value in stats.items():
            # Название характеристики
            stat_text = pixel_font_small.render(stat, True, WHITE)
            surface.blit(stat_text, (panel_rect.x + 15, panel_rect.y + y_offset))

            # Полоска значения
            bar_width = 170
            filled_width = (value / 100) * bar_width
            pygame.draw.rect(surface, (50, 50, 80), (panel_rect.x + 15, panel_rect.y + y_offset + 25, bar_width, 15))
            pygame.draw.rect(surface, self.get_stat_color(stat),
                             (panel_rect.x + 15, panel_rect.y + y_offset + 25, filled_width, 15))

            # Числовое значение
            value_text = pixel_font_small.render(f"{value}%", True, WHITE)
            surface.blit(value_text,
                         (panel_rect.x + bar_width - value_text.get_width() + 15, panel_rect.y + y_offset + 25))

            y_offset += 50

    def get_stat_color(self, stat):
        colors = {
            "Отвага": (0, 200, 0),
            "ПТСР": (200, 0, 0),
            "Блядство": (0, 100, 200),
            "ЧСВ": (200, 200, 0)
        }
        return colors.get(stat, WHITE)

    def draw_actions_panel(self, surface):
        panel_rect = pygame.Rect(50, 50, 150, HEIGHT - 470)
        pygame.draw.rect(surface, (30, 30, 60), panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)

        # Кнопка "Действия" с эффектом наведения
        btn_color = BUTTON_HOVER if self.act_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, self.act_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.act_btn, 1, border_radius=5)
        text = pixel_font_small.render("Действия", True, WHITE)
        surface.blit(text, (self.act_btn.centerx - text.get_width() // 2,
                            self.act_btn.centery - text.get_height() // 2))

        # Кнопка "Инвентарь" с эффектом наведения
        btn_color = BUTTON_HOVER if self.inv_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, self.inv_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.inv_btn, 1, border_radius=5)
        text = pixel_font_small.render("Инвентарь", True, WHITE)
        surface.blit(text, (self.inv_btn.centerx - text.get_width() // 2,
                            self.inv_btn.centery - text.get_height() // 2))

        # Кнопка "Настройки" с эффектом наведения
        btn_color = BUTTON_HOVER if self.sett_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, self.sett_btn, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.sett_btn, 1, border_radius=5)
        text = pixel_font_small.render("Настройки", True, WHITE)
        surface.blit(text, (self.sett_btn.centerx - text.get_width() // 2,
                            self.sett_btn.centery - text.get_height() // 2))

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

    def draw_inventory(self, surface):
        inv_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400)
        pygame.draw.rect(surface, (20, 20, 50), inv_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, inv_rect, 2, border_radius=10)

        title = pixel_font_large.render("Инвентарь", True, WHITE)
        surface.blit(title, (inv_rect.centerx - title.get_width() // 2, inv_rect.y + 20))

        # Отрисовываем предметы из инвентаря
        inventory = game_ui.save_system.get_inventory()
        y_offset = 70
        for item in inventory:
            text = pixel_font_small.render(item, True, WHITE)
            surface.blit(text, (inv_rect.x + 20, inv_rect.y + y_offset))
            y_offset += 30

        # Обновляем позицию кнопки закрытия
        self.inv_close_btn.update(inv_rect.right - 40, inv_rect.y + 10, 30, 30)

        # Кнопка закрытия с эффектом наведения
        btn_color = (230, 80, 80) if self.inv_close_hovered else (200, 50, 50)
        pygame.draw.rect(surface, btn_color, self.inv_close_btn, border_radius=15)
        close_text = pixel_font_small.render("X", True, WHITE)
        surface.blit(close_text, (self.inv_close_btn.centerx - close_text.get_width() // 2,
                                  self.inv_close_btn.centery - close_text.get_height() // 2))

    def draw_settings(self, surface):
        self.settings.draw(surface, WIDTH, HEIGHT, pixel_font_large, pixel_font_small, WHITE, BUTTON_COLOR)

    def draw_actions(self, surface):
        act_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 200, 400, 400)
        pygame.draw.rect(surface, (20, 20, 50), act_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, act_rect, 2, border_radius=10)

        title = pixel_font_large.render("Действия", True, WHITE)
        surface.blit(title, (act_rect.centerx - title.get_width() // 2, act_rect.y + 20))

        # Отрисовываем доступные действия
        actions = game_ui.save_system.get_available_actions()
        y_offset = 70
        for action in actions:
            # Проверяем наведение на действие
            action_rect = pygame.Rect(act_rect.x + 20, act_rect.y + y_offset, 360, 30)
            is_hovered = action_rect.collidepoint(pygame.mouse.get_pos())

            # Рисуем кнопку действия
            btn_color = BUTTON_HOVER if is_hovered else BUTTON_COLOR
            pygame.draw.rect(surface, btn_color, action_rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, action_rect, 1, border_radius=5)

            text = pixel_font_small.render(action, True, WHITE)
            surface.blit(text, (action_rect.x + 10, action_rect.y + 5))

            y_offset += 40

        # Обновляем позицию кнопки закрытия
        self.act_close_btn.update(act_rect.right - 40, act_rect.y + 10, 30, 30)

        # Кнопка закрытия с эффектом наведения
        btn_color = (230, 80, 80) if self.act_close_hovered else (200, 50, 50)
        pygame.draw.rect(surface, btn_color, self.act_close_btn, border_radius=15)
        close_text = pixel_font_small.render("X", True, WHITE)
        surface.blit(close_text, (self.act_close_btn.centerx - close_text.get_width() // 2,
                                  self.act_close_btn.centery - close_text.get_height() // 2))

    def handle_click(self, pos):
        # Сначала проверяем диалоги
        if self.dialog_manager.handle_click(pos):
            return True

        self.last_click_pos = pos

        # Проверяем клики по кнопкам панели действий
        if self.act_btn.collidepoint(pos):
            self.show_actions = not self.show_actions
            self.show_inventory = False
            self.show_settings = False
            return True

        elif self.inv_btn.collidepoint(pos):
            self.show_inventory = not self.show_inventory
            self.show_actions = False
            self.show_settings = False
            return True

        elif self.sett_btn.collidepoint(pos):
            self.show_settings = not self.show_settings
            self.show_actions = False
            self.show_inventory = False
            return True

        # Проверяем клики в открытых окнах
        if self.show_actions and hasattr(self, 'act_close_btn'):
            if self.act_close_btn.collidepoint(pos):
                self.show_actions = False
                return True

        if self.show_inventory and hasattr(self, 'inv_close_btn'):
            if self.inv_close_btn.collidepoint(pos):
                self.show_inventory = False
                return True

        if self.show_settings:
            # Обработка кликов по настройкам
            result = self.settings.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': pos}))
            if result == "close":
                self.show_settings = False
                return True
            elif result == "toggle_fullscreen":
                apply_settings()
                return True
            elif result == "save":
                apply_settings()
                return True

            # Проверяем клик по кнопке закрытия
            if hasattr(self.settings, 'sett_close_btn') and self.settings.sett_close_btn.collidepoint(pos):
                self.show_settings = False
                return True

        return False

    def check_hover(self, pos):
        """Проверяет наведение на элементы UI"""
        self.act_hovered = self.act_btn.collidepoint(pos)
        self.inv_hovered = self.inv_btn.collidepoint(pos)
        self.sett_hovered = self.sett_btn.collidepoint(pos)

        # Кнопки закрытия
        if self.show_actions:
            self.act_close_hovered = self.act_close_btn.collidepoint(pos)
        if self.show_inventory:
            self.inv_close_hovered = self.inv_close_btn.collidepoint(pos)

        # Элементы настроек
        if self.show_settings:
            self.settings.check_hover(pos)

        # Проверяем наведение на кнопки закрытия только если окна открыты
        if self.show_actions:
            self.act_close_hovered = self.act_close_btn.collidepoint(pos)
        else:
            self.act_close_hovered = False

        if self.show_inventory:
            self.inv_close_hovered = self.inv_close_btn.collidepoint(pos)
        else:
            self.inv_close_hovered = False

class GameSaveSystem:
    def __init__(self):
        self.save_file = "game_save.json"
        self.default_data = {
            "inventory": [],
            "actions": [],
            "story_flags": {},
            "completed_actions": set(),
            "current_dialog": "start",
            "character_stats": {
                "Отвага": 60,
                "ПТСР": 30,
                "Блядство": 20,
                "ЧСВ": 60
            }
        }
        self.current_data = self.default_data.copy()

    def load_game(self) -> bool:
        """Загружает сохранение из файла, возвращает True если успешно"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Конвертируем completed_actions из списка в множество
                    if "completed_actions" in loaded_data:
                        loaded_data["completed_actions"] = set(loaded_data["completed_actions"])
                    self.current_data.update(loaded_data)
                return True
            return False
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def save_game(self):
        """Сохраняет текущее состояние игры в файл"""
        # Конвертируем completed_actions в список для сохранения
        save_data = self.current_data.copy()
        save_data["completed_actions"] = list(save_data["completed_actions"])

        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

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

def start_shake(intensity=3, duration=10):
    global shake_intensity, shake_duration
    shake_intensity = intensity
    shake_duration = duration

def update_shake():
    global shake_offset, shake_intensity, shake_duration
    if shake_duration > 0:
        shake_offset[0] = random.randint(-shake_intensity, shake_intensity)
        shake_offset[1] = random.randint(-shake_intensity, shake_intensity)
        shake_duration -= 1
    else:
        shake_offset = [0, 0]

def add_particles():
    for _ in range(20):
        angle = random.uniform(0, 6.28)
        speed = random.uniform(1, 5)
        particles.append([
            target_star[0], target_star[1],
            math.cos(angle) * speed, math.sin(angle) * speed,
            random.randint(1, 3),
            random.randint(10, 30)  # Время жизни
        ])

def play_action():
    global current_state, zoom_factor
    current_state = GameState.ZOOM
    zoom_factor = 1.0
    if stars:
        target_star[:] = random.choice(stars)[:2]
    add_particles()

def quit_action():
    pygame.quit()
    sys.exit()

def start_story():
    """Начинает историю, запуская первый диалог"""
    game_ui.dialog_manager.start_dialog("start", game_ui.settings.get("language", "ru"))

def show_settings_menu():
    global show_main_settings
    show_main_settings = True

# Загрузка и применение начальных настроек
def apply_settings():
    settings = game_ui.settings.settings
    # Применяем настройки громкости
    # Здесь можно добавить код для управления звуком, например:
    # pygame.mixer.music.set_volume(settings.get("music_volume", 0.5))

    # Применяем полноэкранный режим
    if settings.get("fullscreen", False):
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

def restart_game():
    """Полная перезагрузка игры"""
    pygame.quit()
    python = sys.executable
    args = sys.argv
    # Особенная обработка для pyinstaller
    if getattr(sys, 'frozen', False):
        args = [sys.executable]
    os.execl(python, python, *args)

def draw_background(screen, current_state, stars, particles, zoom_factor, target_star, WIDTH, HEIGHT, WHITE):
    """Отрисовывает фон: звезды, частицы и эффекты"""
    # Рисуем звёзды
    if current_state == GameState.ZOOM:
        for star in stars:
            x = (star[0] - target_star[0]) * zoom_factor + target_star[0]
            y = (star[1] - target_star[1]) * zoom_factor + target_star[1]
            size = star[2] * zoom_factor

            if -size < x < WIDTH + size and -size < y < HEIGHT + size:
                pygame.draw.circle(screen, WHITE, (int(x), int(y)), int(size))
    else:
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), star[2])

    # Рисуем частицы
    for p in particles:
        pygame.draw.circle(screen, WHITE, (int(p[0]), int(p[1])), p[4])

    # Эффект туннеля при зуме
    if current_state == GameState.ZOOM:
        zoom_rect = pygame.Rect(0, 0, WIDTH / zoom_factor, HEIGHT / zoom_factor)
        zoom_rect.center = target_star
        zoom_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(zoom_surface, (0, 0, 0, 200), zoom_surface.get_rect())
        pygame.draw.rect(zoom_surface, (0, 0, 0, 0), zoom_rect)
        screen.blit(zoom_surface, (0, 0))

# Инициализация Pygame
pygame.init()

# Настройки окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Рой Мяустанг")
# Шрифты
pixel_font_large = pygame.font.SysFont("Courier New", 36, bold=True)
pixel_font_small = pygame.font.SysFont("Courier New", 16, bold=True)

# Звёзды
stars = []
for _ in range(200):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    size = random.randint(1, 3)
    speed = random.uniform(0.1, 0.5)
    stars.append([x, y, size, speed])



# Эффект дрожания
shake_offset = [0, 0]
shake_intensity = 0
shake_duration = 0


current_state = GameState.MENU
show_main_settings = False

# Эффект зума
zoom_factor = 1.0
max_zoom = 20.0
zoom_speed = 0.1
target_star = [WIDTH // 2, HEIGHT // 2]
zoom_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)

# Частицы
particles = []

buttons = [
    Button(WIDTH // 2 - 100, HEIGHT // 2 - 60, 200, 50, "Играть", play_action),
    Button(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 50, "Настройки", show_settings_menu),
    Button(WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 50, "Выход", quit_action)
]

# Главный цикл
clock = pygame.time.Clock()
running = True
game_ui = GameUI()
music_player = MusicPlayer("music", game_ui.settings.get_music_volume())
music_player.play()


# Применяем настройки при старте
apply_settings()

# Основаной цикл
while running:
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get()  # Get all events once per frame

    # Update game systems
    game_ui.dialog_manager.update()
    update_shake()
    music_player.update(events)  # Handle music events

    # Handle events
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:  # M - mute/unmute
                if pygame.mixer.music.get_volume() > 0:
                    music_player.set_volume(0)
                else:
                    music_player.set_volume(0.5)
            elif event.key == pygame.K_RIGHT and current_state == GameState.PLAY:  # Next track
                if game_ui.dialog_manager.current_text or game_ui.dialog_manager.question:
                    game_ui.dialog_manager.next()
            elif event.key == pygame.K_LEFT and current_state == GameState.PLAY:  # Previous dialog
                if game_ui.dialog_manager.current_text or game_ui.dialog_manager.question:
                    game_ui.dialog_manager.previous()
            elif event.key == pygame.K_SPACE and current_state == GameState.PLAY:
                if game_ui.dialog_manager.current_text or game_ui.dialog_manager.question:
                    game_ui.dialog_manager.next()
            elif event.key == pygame.K_ESCAPE and current_state == GameState.PLAY:
                current_state = GameState.MENU
            elif event.key == pygame.K_i and current_state == GameState.PLAY:
                game_ui.show_inventory = not game_ui.show_inventory
                game_ui.show_settings = False
                game_ui.show_actions = False
            elif event.key == pygame.K_s and current_state == GameState.PLAY:
                game_ui.show_settings = not game_ui.show_settings
                game_ui.show_inventory = False
                game_ui.show_actions = False
            elif event.key == pygame.K_a and current_state == GameState.PLAY:
                game_ui.show_actions = not game_ui.show_actions
                game_ui.show_inventory = False
                game_ui.show_settings = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_ui.dialog_manager.is_show_ending:
                game_ui.dialog_manager.handle_ending_click(event.pos)
            elif show_main_settings:
                result = game_ui.settings.handle_event(event)
                if result == "close":
                    show_main_settings = False
                elif result == "toggle_fullscreen":
                    apply_settings()
                elif result == "save":
                    apply_settings()
            elif current_state == GameState.PLAY:
                if not game_ui.handle_click(event.pos):
                    print(f"Clicked at: {event.pos}")
            elif current_state == GameState.MENU and not show_main_settings:
                for button in buttons:
                    button.handle_event(event)

    # Update game state
    if current_state == GameState.ZOOM:
        zoom_factor += zoom_speed
        if zoom_factor >= max_zoom:
            current_state = GameState.PLAY
            zoom_factor = 1.0
            start_story()

    # Update stars
    for star in stars:
        star[1] += star[3] * (zoom_factor ** 0.5)
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)

    # Update particles
    for p in particles[:]:
        p[0] += p[2]
        p[1] += p[3]
        p[5] -= 1
        if p[5] <= 0:
            particles.remove(p)

    # Check button hovers in menu
    if current_state == GameState.MENU:
        for button in buttons:
            button.check_hover(mouse_pos)
        if any(btn.is_hovered for btn in buttons) and random.random() < 0.1:
            start_shake(1, 5)

    # Drawing
    screen.fill(BLUE_DARK)
    draw_background(screen, current_state, stars, particles, zoom_factor, target_star, WIDTH, HEIGHT, WHITE)

    if current_state == GameState.ZOOM:
        zoom_rect.width = WIDTH / zoom_factor
        zoom_rect.height = HEIGHT / zoom_factor
        zoom_rect.center = target_star
        zoom_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(zoom_surface, (0, 0, 0, 200), zoom_surface.get_rect())
        pygame.draw.rect(zoom_surface, (0, 0, 0, 0), zoom_rect)
        screen.blit(zoom_surface, (0, 0))

    # Draw current game state
    if current_state == GameState.MENU:
        # Draw title
        title_color = (255, 255, 255) if pygame.time.get_ticks() % 1000 < 500 else (100, 100, 255)
        title = pixel_font_large.render("Рой Мяустанг", True, title_color)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        # Draw buttons
        for button in buttons:
            original_pos = button.rect.topleft
            button.rect.topleft = (original_pos[0] + shake_offset[0], original_pos[1] + shake_offset[1])
            button.draw(screen)
            button.rect.topleft = original_pos

        if show_main_settings:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            game_ui.draw_settings(screen)
            game_ui.settings.check_hover(mouse_pos)

    elif current_state == GameState.ZOOM and zoom_factor >= max_zoom * 0.9:
        alpha = int(255 * (zoom_factor - max_zoom * 0.9) / (max_zoom * 0.1))
        transition = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        transition.fill((0, 0, 0, alpha))
        screen.blit(transition, (0, 0))

    elif current_state == GameState.PLAY:
        game_ui.draw(screen)
        game_ui.check_hover(mouse_pos)

    pygame.display.flip()
    clock.tick(60)

# Save settings before quitting
game_ui.settings.save_settings()
pygame.quit()
sys.exit()