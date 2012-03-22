#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from xbmcswift import Plugin, xbmc, xbmcplugin, xbmcgui, clean_dict
import resources.lib.scraper as scraper

__addon_name__ = 'MyVideo.de'
__id__ = 'plugin.video.myvideo_de'

DEBUG = False


class Plugin_mod(Plugin):

    def add_items(self, iterable, is_update=False, sort_method_ids=[],
                  override_view_mode=False):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))
        if self._mode is 'xbmc':
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            if override_view_mode:
                if xbmc.getSkinDir() == 'skin.confluence':
                    cmd = 'Container.SetViewMode(%s)' % 500
                    xbmc.executebuiltin(cmd)
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)
        return urls

    def _make_listitem(self, label, label2='', iconImage='', thumbnail='',
                       path='', **options):
        li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage,
                              thumbnailImage=thumbnail, path=path)
        cleaned_info = clean_dict(options.get('info'))
        if cleaned_info:
            li.setInfo('video', cleaned_info)
        if options.get('is_playable'):
            li.setProperty('IsPlayable', 'true')
        if options.get('context_menu'):
            li.addContextMenuItems(options['context_menu'])
        return options['url'], li, options.get('is_folder', True)

plugin = Plugin_mod(__addon_name__, __id__, __file__)


@plugin.route('/', default=True)
def show_categories():
    __log('show_categories start')
    entries = scraper.get_categories()
    items = [{'label': e['title'],
              'url': plugin.url_for('show_subcategories',
                                    path=e['path'])}
             for e in entries]
    items.append({'label': plugin.get_string(30001),
                  'url': plugin.url_for('video_search')})
    __log('show_categories end')
    return plugin.add_items(items)


@plugin.route('/search/')
def video_search():
    __log('search start')
    keyboard = xbmc.Keyboard('', 'Video Suche')
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        __log('search gots a string: "%s"' % search_string)
        entries = scraper.get_search_result(search_string)
        __log('search end')
        return __add_items(entries)


@plugin.route('/category/<path>/')
def show_subcategories(path):
    __log('show_subcategories start')
    entries = scraper.get_sub_categories(path)
    items = [{'label': e['title'],
              'url': plugin.url_for('show_path',
                                    path=e['path'])}
             for e in entries]
    __log('show_subcategories end')
    return plugin.add_items(items)


@plugin.route('/<path>/')
def show_path(path):
    __log('show_path started with path: %s' % path)
    entries = scraper.get_path(path)
    __log('show_path end')
    return __add_items(entries)


def __add_items(entries):
    items = []
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED, ]
    is_update = False
    for e in entries:
        if e.get('pagenination', False):
            if e['pagenination'] == 'PREV':
                is_update = True
                title = '<< %s %s <<' % (plugin.get_string(30000), e['title'])
            elif e['pagenination'] == 'NEXT':
                title = '>> %s %s >>' % (plugin.get_string(30000), e['title'])
            items.append({'label': title,
                          'iconImage': 'DefaultFolder.png',
                          'is_folder': True,
                          'is_playable': False,
                          'url': plugin.url_for('show_path',
                                                path=e['path'])})
        elif e['is_folder']:
            items.append({'label': e['title'],
                          'iconImage': e.get('thumb', 'DefaultFolder.png'),
                          'is_folder': True,
                          'is_playable': False,
                          'url': plugin.url_for('show_path',
                                                path=e['path'])})
        else:
            items.append({'label': e['title'],
                          'iconImage': e.get('thumb', 'DefaultVideo.png'),
                          'info': {'duration': e.get('length', '0:00'),
                                   'plot': e.get('description', ''),
                                   'studio': e.get('username', ''),
                                   'date': e.get('date'),
                                   'year': e.get('year'),
                                   'rating': e.get('rating'),
                                   'votes': e.get('votes'),
                                   'views': e.get('views')},
                          'is_folder': False,
                          'is_playable': True,
                          'url': plugin.url_for('watch_video',
                                                video_id=e['video_id'])})
    sort_methods.extend((xbmcplugin.SORT_METHOD_VIDEO_RATING,
                         xbmcplugin.SORT_METHOD_VIDEO_RUNTIME,))
    __log('__add_items end')
    return plugin.add_items(items, is_update=is_update,
                            sort_method_ids=sort_methods,
                            override_view_mode=False)


@plugin.route('/video/<video_id>/')
def watch_video(video_id):
    __log('watch_video started with video_id: %s' % video_id)
    video_url = scraper.get_video(video_id)
    __log('watch_video finished with url: %s' % video_url)
    return plugin.set_resolved_url(video_url)


def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))


if __name__ == '__main__':
    plugin.run()
