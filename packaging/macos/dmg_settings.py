# -*- coding: utf-8 -*-
# dmgbuild 配置:带三虎插画背景的安装窗口(把 Sanhuu.app 拖进"应用程序")
import os
ROOT = os.getcwd()
files = [os.path.join(ROOT, 'dist', 'Sanhuu.app')]
symlinks = {'Applications': '/Applications'}
icon = os.path.join(ROOT, 'assets', 'icon.icns')
background = os.path.join(ROOT, 'assets', 'installer', 'dmg_background.png')
window_rect = ((200, 120), (660, 450))
default_view = 'icon-view'
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
icon_size = 110
text_size = 13
icon_locations = {'Sanhuu.app': (150, 205), 'Applications': (510, 205)}
format = 'UDZO'
