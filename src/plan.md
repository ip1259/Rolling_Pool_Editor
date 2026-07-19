# ChanceWeightEditorApp v2 重構計畫
> 目標：保持現有功能 100% 相容，在不修改 GameParam / GameText API 的前提下，提升大型資料表 (1000~5000 筆) 的 UI 渲染效率、可維護性與擴充性。

---

# Version
Target : v2.0

Python : 3.11+

GUI : CustomTkinter

Compatible :
- GameParam.py
- GameText.py

---

# 重構目標

目前：

```
修改 Weight

↓

update_weight()

↓

update_chance_rate_map()

↓

refresh_data_grid()

↓

整張 Table 全部 Configure
```

改為

```
修改 Weight

↓

update_weight()

↓

update_chance_rate_map()

↓

refresh_visible_rows()

↓

只更新畫面需要更新的內容
```

---

# Architecture

```
ChanceWeightEditorApp
│
├── ThemeManagerCache
├── LocalizationCache
├── FilterTree
├── TableController
│      │
│      ├── HeaderRenderer
│      ├── RowRenderer
│      ├── VirtualTable
│      └── ObjectPool
│
├── WarningController
├── ExportController
└── EventDispatcher
```

---

# 專案結構

```
main.py

↓

editor/

    app.py

    table_renderer.py

    table_pool.py

    virtual_table.py

    theme_cache.py

    localization_cache.py

    filter_controller.py

    event_controller.py

    warning_controller.py
```

若保持單檔

```
ChanceWeightEditorApp

↓

Theme

↓

Layout

↓

Filter

↓

Renderer

↓

Events

↓

Export
```

依區塊重新整理。

---

# Renderer 重構

目前

```
refresh_data_grid()

約 300 行
```

拆成

```
refresh_data_grid()

↓

_build_display_records()

↓

_refresh_headers()

↓

_refresh_rows()

↓

_hide_unused_rows()

↓

_update_warning()
```

---

# Header Renderer

目前

Header 每次 Refresh

↓

全部 Configure

修改

Header 僅在

Language Changed

Theme Changed

更新。

Weight 修改

↓

完全不更新 Header。

---

# Row Renderer

新增

```
_update_row()

_update_entry()

_update_chance()

_update_colors()

_update_lock_state()
```

避免所有 configure() 混在一起。

---

# Theme Cache

新增

```
class ThemeCache
```

初始化

```
text

header

odd_row

even_row

warning

locked

chance

button

entry
```

Theme Changed

↓

重新 Cache

Refresh

↓

直接使用

```
self.theme.header_bg
```

不再查 ThemeManager。

---

# Localization Cache

目前

```
GameText.AttachEffect[]

GameText.Menu[]
```

每列都查詢。

新增

```
effect_name_cache

filter_name_cache

menu_cache
```

Language Changed

↓

一次重建 Cache。

Table Refresh

↓

Dictionary Lookup。

---

# Virtual Table

目前

```
1000 Row

↓

1000 Widget
```

改

```
Visible

約 28 Row

↓

永遠只有

28 Widget
```

Scroll

↓

更新文字

↓

不是 Create Widget。

---

# Object Pool

目前

```
Widget Pool
```

保留。

修改

Pool

↓

Virtual Pool

固定

```
30~40

Rows
```

---

# Widget 更新策略

目前

```
configure()

永遠執行
```

修改

```
if old != new:

    configure()
```

例如

```
Chance

Name

Tag

Weight

FinalWeight
```

全部比對。

---

# Entry 更新

目前

```
delete()

insert()
```

每次都做。

修改

```
if value changed

↓

delete

↓

insert
```

---

# Save Button

目前

```
lambda

每次建立
```

修改

```
partial()

或

固定 callback
```

Object Pool 建立一次。

---

# Entry 驗證

目前

```
try

int()

except
```

改

```
validatecommand
```

只允許

```
0-9

-

```

避免 Exception。

---

# Scroll

目前

CTkScrollableFrame

↓

全部 Widget。

修改

Canvas

↓

Virtual Scroll

↓

Visible Widgets。

---

# Table 顯示

新增

交錯色

```
Light

Dark
```

Hover

```
Mouse Enter

↓

Highlight Row
```

Selected Row

```
Border

Accent Color
```

---

# Warning

目前

```
refresh_data_grid()

↓

_update_warning()
```

拆分

```
WarningController
```

Weight 更新

↓

直接更新。

---

# Export

拆成

```
_export_dialog()

↓

_validate()

↓

_export_csv()

↓

_show_result()
```

---

# Event

目前

全部事件散落。

整理

```
Theme Changed

↓

Language Changed

↓

Filter Changed

↓

Weight Changed

↓

Table Changed

↓

Export
```

每個事件獨立。

---

# 效能優化

## Configure 最小化

目前

```
800 rows

×

7 labels

=

5600 configure
```

改

```
只有改變的 configure
```

---

## Dictionary Cache

全部

```
GameText

↓

Cache
```

---

## Theme Cache

全部

```
ThemeManager

↓

ThemeCache
```

---

## Chance

Weight 更新

↓

只重新算

Chance

↓

不用重建 Widget。

---

## Entry

只更新

Visible。

---

# Visual

新增

✓ Zebra Row

✓ Hover

✓ Selected Row

✓ Better Header

✓ Rounded Header

✓ Better Warning Bar

✓ Better Button Style

✓ Consistent Padding

✓ Better Column Alignment

---

# 程式碼規範

全部加入

Type Hint

```
Dict

List

Optional

Callable
```

全部 Function

增加 Docstring。

---

# TODO

## Phase 1

- [ ] Theme Cache
- [ ] Localization Cache
- [ ] Renderer 分離
- [ ] Header Renderer
- [ ] Row Renderer

---

## Phase 2

- [ ] Configure 最小化
- [ ] Entry 更新最佳化
- [ ] Callback 重構
- [ ] Warning Controller

---

## Phase 3

- [ ] Virtual Table
- [ ] Virtual Scroll
- [ ] Visible Object Pool
- [ ] Hover Effect
- [ ] Selected Row

---

## Phase 4

- [ ] Export 重構
- [ ] Event Dispatcher
- [ ] Layout Cleanup
- [ ] Code Cleanup
- [ ] Full Comment
- [ ] Documentation

---

# 預期成果

目前

```
refresh_data_grid()

約 300 行

整體

約 900 行
```

完成後

```
refresh_data_grid()

約 40~60 行

Renderer

完全模組化

UI

可支援

3000~5000+

資料

仍保持流暢。
```