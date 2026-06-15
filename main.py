import os

from kivy.app import App
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy_garden.mapview import MapLayer, MapMarker
import models
from utils import compute_route, format_route

KV = 'ui.kv'


class StreetItem(BoxLayout):
    street_id = NumericProperty(0)
    street_name = StringProperty('')
    units = StringProperty('')

    def on_done(self):
        app = App.get_running_app()
        if app and app.root:
            user_screen = app.root.get_screen('user')
            if user_screen and self.street_id:
                user_screen.mark_street_done(self.street_id)


class RouteLayer(MapLayer):
    def __init__(self, points=None, **kwargs):
        super().__init__(**kwargs)
        self.points = points or []
        self.line = None

    def reposition(self):
        if not self.points or not getattr(self, 'parent', None):
            return
        self.canvas.clear()
        if not self.parent:
            return
        coords = []
        for lat, lon in self.points:
            x, y = self.parent.get_window_xy_from(lat, lon, self.parent.zoom)
            coords.extend([x, y])
        if coords:
            with self.canvas:
                Color(0, 0.6, 1, 0.8)
                self.line = Line(points=coords, width=2)


class LoginScreen(Screen):
    selected_role = StringProperty('')
    roles = ListProperty(['manager', 'supervisor', 'user'])
    supervisors = ListProperty([])
    users = ListProperty([])
    selected_supervisor_name = StringProperty('')
    selected_user_name = StringProperty('')
    login_message = StringProperty('Choose a role and sign in.')

    def on_pre_enter(self):
        self.refresh_lists()
        self.login_message = 'Choose a role and sign in.'

    def refresh_lists(self):
        """Clear all fields and reload."""
        self.selected_role = ''
        self.selected_supervisor_name = ''
        self.selected_user_name = ''
        self.login_message = 'Choose a role and sign in.'
        self.supervisors = models.get_supervisors()
        self.users = models.get_users()

    def on_role_selected(self, role):
        self.selected_role = role
        if role == 'supervisor':
            self.selected_supervisor_name = ''
        elif role == 'user':
            self.selected_user_name = ''

    def login(self):
        app = App.get_running_app()
        if not self.selected_role:
            self.login_message = 'Please select a role.'
            return
        if self.selected_role == 'manager':
            app.login_manager()
            return
        if self.selected_role == 'supervisor':
            supervisor = next((s for s in self.supervisors if s['name'] == self.selected_supervisor_name), None)
            if not supervisor:
                self.login_message = 'Select a supervisor.'
                return
            app.login_supervisor(supervisor['id'])
            return
        if self.selected_role == 'user':
            user = next((u for u in self.users if u['name'] == self.selected_user_name), None)
            if not user:
                self.login_message = 'Select a user.'
                return
            app.login_user(user['id'])
            return


class ManagerScreen(Screen):
    supervisors = ListProperty([])
    supervisor_names = ListProperty([])
    areas = ListProperty([])
    users = ListProperty([])
    campaigns = ListProperty([])
    campaign_caches = ListProperty([])
    campaign_cache_messages = ListProperty([])
    regions = ListProperty([])
    provinces = ListProperty([])
    districts = ListProperty([])
    cities = ListProperty([])
    geo_areas = ListProperty([])
    selected_supervisor_name = StringProperty('')
    message = StringProperty('')
    new_supervisor_name = StringProperty('')
    selected_campaign = StringProperty('')
    selected_region = StringProperty('')
    selected_province = StringProperty('')
    selected_district = StringProperty('')
    selected_city = StringProperty('')
    selected_area = StringProperty('')
    show_supervisor_input = BooleanProperty(False)
    summary_text = StringProperty('')
    # Campaign creation fields
    new_campaign_name = StringProperty('')
    new_campaign_packs = StringProperty('10')
    new_campaign_units = StringProperty('100')
    show_campaign_input = BooleanProperty(False)

    def on_pre_enter(self):
        self.refresh_lists()

    def refresh_lists(self, clear=False):
        if clear:
            self.selected_supervisor_name = ''
            self.selected_campaign = ''
            self.selected_region = ''
            self.selected_province = ''
            self.selected_district = ''
            self.selected_city = ''
            self.selected_area = ''
            self.new_supervisor_name = ''
            self.message = ''
            self.show_supervisor_input = False
            self.provinces = []
            self.districts = []
            self.cities = []
            self.geo_areas = []

        self.supervisors = models.get_supervisors()
        self.supervisor_names = [s['name'] for s in self.supervisors]
        self.areas = models.get_areas()
        self.users = models.get_users()
        self.campaigns = models.get_campaigns()
        self.campaign_caches = models.get_campaign_cache_entries()
        self.campaign_cache_messages = [
            f"{cache['campaign_name'] or 'No campaign'} -> {cache['supervisor_name'] or 'No supervisor'} -> {cache['neighborhood_name'] or 'No neighborhood'}"
            for cache in self.campaign_caches
        ]
        self.regions = models.get_regions()
        # Uniform Belgian hierarchy: Region → Province → District → City → Area
        if self.selected_region:
            region = next((r for r in self.regions if r['name'] == self.selected_region), None)
            if region:
                self.provinces = models.get_provinces(region['id'])
        if self.selected_province:
            province = next((p for p in self.provinces if p['name'] == self.selected_province), None)
            if province:
                self.districts = models.get_cities(province['id'])  # cities table holds districts/arrondissements
        if self.selected_district:
            district = next((d for d in self.districts if d['name'] == self.selected_district), None)
            if district:
                self.cities = models.get_municipalities(district['id'])  # municipalities table holds cities
        if self.selected_city:
            city = next((c for c in self.cities if c['name'] == self.selected_city), None)
            if city:
                self.geo_areas = models.get_neighborhoods(city['id'])  # neighborhoods table holds areas
        self._update_summary()

    def _update_summary(self):
        """Build summary line showing current selections."""
        parts = []
        if self.selected_campaign:
            parts.append(f"Campaign: {self.selected_campaign}")
        if self.selected_supervisor_name:
            parts.append(f"Supervisor: {self.selected_supervisor_name}")
        if self.selected_area:
            parts.append(f"Area: {self.selected_area}")
        self.summary_text = '  |  '.join(parts) if parts else 'No selections yet'

    def on_region_selected(self, region_name):
        self.selected_region = region_name
        region = next((r for r in self.regions if r['name'] == region_name), None)
        if region:
            self.provinces = models.get_provinces(region['id'])
            self.selected_province = ''
            self.selected_district = ''
            self.selected_city = ''
            self.selected_area = ''
            self.districts = []
            self.cities = []
            self.geo_areas = []
        self._update_summary()

    def on_province_selected(self, province_name):
        self.selected_province = province_name
        province = next((p for p in self.provinces if p['name'] == province_name), None)
        if province:
            self.districts = models.get_cities(province['id'])  # cities table holds districts
            self.selected_district = ''
            self.selected_city = ''
            self.selected_area = ''
            self.cities = []
            self.geo_areas = []
        self._update_summary()

    def on_district_selected(self, district_name):
        self.selected_district = district_name
        district = next((d for d in self.districts if d['name'] == district_name), None)
        if district:
            self.cities = models.get_municipalities(district['id'])  # municipalities table holds cities
            self.selected_city = ''
            self.selected_area = ''
            self.geo_areas = []
        self._update_summary()

    def on_city_selected(self, city_name):
        self.selected_city = city_name
        city = next((c for c in self.cities if c['name'] == city_name), None)
        if city:
            self.geo_areas = models.get_neighborhoods(city['id'])  # neighborhoods table holds areas
            self.selected_area = ''
        self._update_summary()

    def on_campaign_selected(self, campaign_name):
        self.selected_campaign = campaign_name
        self._update_summary()

    def on_area_selected(self, area_name):
        self.selected_area = area_name
        self._update_summary()

    def toggle_supervisor_input(self):
        self.show_supervisor_input = not self.show_supervisor_input
        if not self.show_supervisor_input:
            self.new_supervisor_name = ''
            self.selected_campaign = ''
            self.selected_area = ''

    def create_supervisor(self):
        name = self.new_supervisor_name.strip()
        if not name:
            self.message = 'Enter a supervisor name.'
            return
        campaign = next((c for c in self.campaigns if c['name'] == self.selected_campaign), None)
        area = next((a for a in self.geo_areas if a['name'] == self.selected_area), None)
        
        campaign_id = campaign['id'] if campaign else None
        area_id = area['id'] if area else None
        
        models.add_supervisor(name, campaign_id, area_id)
        self.new_supervisor_name = ''
        self.selected_campaign = ''
        self.selected_area = ''
        self.show_supervisor_input = False
        self.message = f'Supervisor "{name}" added.'
        self.refresh_lists()

    def on_supervisor_selected(self, name):
        self.selected_supervisor_name = name
        self._update_summary()

    def assign_neighborhood(self):
        if not self.selected_campaign:
            self.message = 'Select a campaign first.'
            return
        if not self.selected_supervisor_name:
            self.message = 'Select a supervisor first.'
            return
        supervisor = next((s for s in self.supervisors if s['name'] == self.selected_supervisor_name), None)
        if not supervisor:
            self.message = 'Supervisor not found.'
            return
        area = next((a for a in self.geo_areas if a['name'] == self.selected_area), None)
        campaign = next((c for c in self.campaigns if c['name'] == self.selected_campaign), None)
        if not area:
            self.message = 'Select an area.'
            return
        models.assign_neighborhood_to_supervisor(supervisor['id'], area['id'], campaign['id'])
        # save cache for future campaign
        models.save_campaign_cache(campaign['id'], supervisor['id'], None, None, None, None, area['id'])
        self.message = f"Assigned {area['name']} to {supervisor['name']}."
        self.show_confirmation(self.message)
        self._update_summary()
        self.refresh_lists()

    def toggle_campaign_input(self):
        self.show_campaign_input = not self.show_campaign_input
        if not self.show_campaign_input:
            self.new_campaign_name = ''
            self.new_campaign_packs = '10'
            self.new_campaign_units = '100'

    def create_campaign(self):
        name = self.new_campaign_name.strip()
        if not name:
            self.message = 'Enter a campaign name.'
            return
        try:
            packs = int(self.new_campaign_packs)
            units = int(self.new_campaign_units)
        except ValueError:
            self.message = 'Packs and units must be numbers.'
            return
        if packs <= 0 or units <= 0:
            self.message = 'Packs and units must be positive.'
            return
        models.add_campaign(name, packs, units)
        self.new_campaign_name = ''
        self.new_campaign_packs = '10'
        self.new_campaign_units = '100'
        self.show_campaign_input = False
        self.message = f'Campaign "{name}" created ({packs} packs, {units} units/pack).'
        self.refresh_lists()

    def clear_cache(self):
        app = App.get_running_app()
        dialog_content = BoxLayout(orientation='vertical', spacing='12dp', padding='12dp')
        dialog_content.add_widget(Label(
            text='Clear all cached data?\nCampaigns will be preserved.',
            halign='center',
            valign='middle',
        ))
        button_box = BoxLayout(size_hint_y=None, height='40dp', spacing='12dp')
        button_box.add_widget(Button(text='Cancel', on_release=lambda *a: popup.dismiss()))
        button_box.add_widget(Button(text='Confirm', on_release=lambda *a: self._confirm_clear_cache(popup)))
        dialog_content.add_widget(button_box)
        popup = Popup(title='Confirm Clear Cache', content=dialog_content, size_hint=(0.7, 0.3), auto_dismiss=False)
        popup.open()

    def _confirm_clear_cache(self, popup):
        popup.dismiss()
        models.clear_cache_keep_campaigns()
        self.message = 'Cache cleared. Campaigns preserved.'
        self.refresh_lists(clear=True)

    def show_confirmation(self, message):
        popup = Popup(
            title='Confirmation',
            content=Label(text=message, halign='center', valign='middle', text_size=(300, None)),
            size_hint=(0.7, 0.3),
            auto_dismiss=True,
        )
        popup.open()


class SupervisorScreen(Screen):
    supervisor_id = NumericProperty(0)
    supervisors = ListProperty([])
    users = ListProperty([])
    areas = ListProperty([])
    unassigned = ListProperty([])
    assigned = ListProperty([])
    selected_user = NumericProperty(0)
    selected_supervisor_name = StringProperty('')
    new_user_name = StringProperty('')
    campaign_name = StringProperty('')
    neighborhood_name = StringProperty('')
    message = StringProperty('')
    show_create_user = BooleanProperty(False)
    # New campaign/user management properties
    campaigns = ListProperty([])
    selected_campaign = StringProperty('')
    geo_areas = ListProperty([])
    selected_area = StringProperty('')
    streets = ListProperty([])
    selected_streets = ListProperty([])
    summary_text = StringProperty('')
    selected_user_name = StringProperty('')
    show_create_user_input = BooleanProperty(False)
    street_button_label = StringProperty('Select Streets')

    def on_pre_enter(self):
        app = App.get_running_app()
        if app and app.current_role == 'supervisor' and app.current_profile_id:
            self.supervisor_id = app.current_profile_id
        self.load_supervisor()

    def load_supervisor(self):
        app = App.get_running_app()
        self.supervisors = models.get_supervisors()
        if self.supervisors:
            if app and app.current_role == 'supervisor' and app.current_profile_id:
                current = next((s for s in self.supervisors if s['id'] == app.current_profile_id), None)
                if current:
                    self.selected_supervisor_name = current['name']
                    self.supervisor_id = current['id']
                    if current.get('campaign_id'):
                        campaign = next((c for c in models.get_campaigns() if c['id'] == current['campaign_id']), None)
                        self.campaign_name = campaign['name'] if campaign else ''
                    if current.get('neighborhood_id'):
                        neighborhoods = models.get_neighborhoods()
                        neighborhood = next((n for n in neighborhoods if n['id'] == current['neighborhood_id']), None)
                        self.neighborhood_name = neighborhood['name'] if neighborhood else ''
            if not self.selected_supervisor_name:
                self.selected_supervisor_name = self.supervisors[0]['name']
            self.set_supervisor_by_name(self.selected_supervisor_name)
        else:
            self.selected_supervisor_name = ''
        self.refresh_lists()

    def set_supervisor_by_name(self, name):
        supervisor = next((s for s in self.supervisors if s['name'] == name), None)
        if supervisor:
            self.supervisor_id = supervisor['id']
            self.selected_supervisor_name = supervisor['name']
            if supervisor.get('campaign_id'):
                campaign = next((c for c in models.get_campaigns() if c['id'] == supervisor['campaign_id']), None)
                self.campaign_name = campaign['name'] if campaign else ''
            if supervisor.get('neighborhood_id'):
                neighborhoods = models.get_neighborhoods()
                neighborhood = next((n for n in neighborhoods if n['id'] == supervisor['neighborhood_id']), None)
                self.neighborhood_name = neighborhood['name'] if neighborhood else ''
            app = App.get_running_app()
            if app:
                app.current_role = 'supervisor'
                app.current_profile_id = supervisor['id']
        self.refresh_lists()

    def set_user_by_name(self, name):
        user = next((u for u in self.users if u['name'] == name), None)
        if user:
            self.selected_user = user['id']
            self.selected_user_name = user['name']
        self._update_summary()

    def refresh_lists(self):
        self.users = models.get_users(self.supervisor_id)
        self.areas = models.get_areas(self.supervisor_id)
        self.unassigned = models.get_unassigned_streets(self.supervisor_id)
        self.assigned = models.get_assigned_streets_for_supervisor(self.supervisor_id)
        # Load campaigns assigned to this supervisor
        supervisor = next((s for s in self.supervisors if s['id'] == self.supervisor_id), None)
        if supervisor and supervisor.get('campaign_id'):
            campaign = next((c for c in models.get_campaigns() if c['id'] == supervisor['campaign_id']), None)
            self.campaigns = [campaign] if campaign else []
        else:
            self.campaigns = models.get_campaigns()
        # Populate geo_areas from assigned areas
        self.geo_areas = [a for a in self.areas]
        if self.users and self.selected_user == 0:
            self.selected_user = self.users[0]['id']
            self.selected_user_name = self.users[0]['name']
        self._update_summary()

    def _update_summary(self):
        parts = []
        if self.selected_campaign:
            parts.append(f"Campaign: {self.selected_campaign}")
        if self.selected_area:
            parts.append(f"Area: {self.selected_area}")
        if self.selected_user_name:
            parts.append(f"User: {self.selected_user_name}")
        if self.selected_streets:
            parts.append(f"Streets: {len(self.selected_streets)} selected")
        self.summary_text = '  |  '.join(parts) if parts else 'No selections yet'
        n = len(self.selected_streets)
        self.street_button_label = f'Select Streets ({n} selected)' if n else 'Select Streets'

    def on_campaign_selected(self, name):
        self.selected_campaign = name
        # Load areas for this supervisor under the selected campaign
        self.geo_areas = []
        self.selected_area = ''
        for a in self.areas:
            self.geo_areas.append(a)
        self._update_summary()

    def on_area_selected(self, name):
        self.selected_area = name
        # Get all unassigned streets for this supervisor, then filter by selected area
        all_streets = models.get_unassigned_streets(self.supervisor_id)
        self.streets = [s for s in all_streets if s.get('area_name', '') == name]
        self.selected_streets = []
        self._update_summary()

    def select_streets_popup(self):
        """Open a popup with checkboxes to select streets prefiltered by area."""
        if not self.selected_area:
            self.message = 'Select an area first.'
            return
        if not self.streets:
            self.message = 'No streets available in this area.'
            return

        content = BoxLayout(orientation='vertical', spacing='8dp', padding='12dp')
        content.add_widget(Label(
            text=f'Streets in {self.selected_area}',
            size_hint_y=None, height='40dp', font_size='22sp', bold=True))

        scroll = ScrollView(do_scroll_x=False)
        check_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing='4dp')
        check_layout.bind(minimum_height=check_layout.setter('height'))
        scroll.add_widget(check_layout)
        content.add_widget(scroll)

        # Track selections locally in the popup
        selected_in_popup = set(self.selected_streets)
        checkboxes = []

        def on_confirm(instance):
            self.selected_streets = list(selected_in_popup)
            self._update_summary()
            popup.dismiss()

        for street in self.streets:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height='42dp', spacing='6dp')
            cb = CheckBox(size_hint_x=None, width='40dp', active=street['name'] in selected_in_popup)
            cb.bind(active=lambda cb_instance, value, s=street['name']: (
                selected_in_popup.add(s) if value else selected_in_popup.discard(s)
            ))
            lbl = Label(text=street['name'], font_size='20sp', halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            box.add_widget(cb)
            box.add_widget(lbl)
            check_layout.add_widget(box)
            checkboxes.append(cb)

        btn_box = BoxLayout(size_hint_y=None, height='48dp', spacing='12dp')
        btn_box.add_widget(Button(text='Select All', font_size='20sp',
            on_release=lambda *a: [setattr(cb, 'active', True) for cb in checkboxes]))
        btn_box.add_widget(Button(text='Clear All', font_size='20sp',
            on_release=lambda *a: [setattr(cb, 'active', False) for cb in checkboxes]))
        btn_box.add_widget(Button(text='Confirm', font_size='20sp', on_release=on_confirm))
        content.add_widget(btn_box)

        popup = Popup(title='Select Streets', content=content, size_hint=(0.85, 0.7), auto_dismiss=True)
        popup.open()

    def assign_streets(self):
        if not self.selected_user:
            self.message = 'Select a user first.'
            return
        if not self.selected_streets:
            self.message = 'Select at least one street.'
            return
        unassigned = models.get_unassigned_streets(self.supervisor_id)
        count = 0
        for street in unassigned:
            if street['name'] in self.selected_streets:
                models.assign_street_to_user(street['id'], self.selected_user)
                count += 1
        self.message = f'Assigned {count} street(s) to user.'
        self.selected_streets = []
        self.refresh_lists()

    def toggle_create_user(self):
        self.show_create_user_input = not self.show_create_user_input
        if not self.show_create_user_input:
            self.new_user_name = ''
            self.message = ''

    def create_user(self):
        name = self.new_user_name.strip()
        if not name:
            self.message = 'Enter a user name.'
            return
        models.add_user(name, self.supervisor_id)
        self.new_user_name = ''
        self.message = f'User "{name}" created.'
        self.show_create_user_input = False
        self.refresh_lists()

    def clear_cache(self):
        app = App.get_running_app()
        dialog_content = BoxLayout(orientation='vertical', spacing='12dp', padding='12dp')
        dialog_content.add_widget(Label(
            text='Clear all cached data?\nCampaigns will be preserved.',
            halign='center', valign='middle',
        ))
        button_box = BoxLayout(size_hint_y=None, height='40dp', spacing='12dp')
        button_box.add_widget(Button(text='Cancel', on_release=lambda *a: popup.dismiss()))
        button_box.add_widget(Button(text='Confirm', on_release=lambda *a: self._confirm_clear_cache(popup)))
        dialog_content.add_widget(button_box)
        popup = Popup(title='Confirm Clear Cache', content=dialog_content, size_hint=(0.7, 0.3), auto_dismiss=False)
        popup.open()

    def _confirm_clear_cache(self, popup):
        popup.dismiss()
        models.clear_cache_keep_campaigns()
        self.message = 'Cache cleared.'
        self.refresh_lists()


class UserScreen(Screen):
    user_id = NumericProperty(0)
    user_name = StringProperty('')
    streets = ListProperty([])
    route_text = StringProperty('Route will appear here')
    markers = ListProperty([])

    def on_pre_enter(self):
        app = App.get_running_app()
        if app and app.current_role == 'user' and app.current_profile_id:
            self.user_id = app.current_profile_id
        if self.user_id == 0:
            u = models.get_any_user()
            if u:
                self.user_id = u['id']
                self.user_name = u['name']
        self.load_assignments()

    def load_assignments(self):
        if not self.user_id:
            self.route_text = 'No user selected.'
            return
        self.streets = models.get_streets_for_user(self.user_id)
        self.user_name = next((u['name'] for u in models.get_users() if u['id'] == self.user_id), self.user_name)
        self.route_text = 'Route will appear here'
        if hasattr(self.ids, 'street_list'):
            self.ids.street_list.clear_widgets()
            for street in self.streets:
                widget = StreetItem(street_id=street['id'], street_name=street['name'], units=str(street['units']))
                self.ids.street_list.add_widget(widget)
        self.update_map()

    def clear_map_overlays(self):
        if hasattr(self.ids, 'map_view'):
            for marker in list(self.markers):
                try:
                    self.ids.map_view.remove_marker(marker)
                except Exception:
                    pass
            self.markers = []
        if hasattr(self, 'route_layer') and self.route_layer:
            try:
                self.ids.map_view.remove_layer(self.route_layer)
            except Exception:
                pass
            self.route_layer = None

    def update_map(self, route_coords=None):
        self.clear_map_overlays()
        if not hasattr(self.ids, 'map_view'):
            return
        points = []
        if route_coords:
            points = route_coords
        else:
            points = [(s['lat'], s['lon']) for s in self.streets if s['lat'] is not None and s['lon'] is not None]
        for lat, lon in points:
            marker = MapMarker(lat=lat, lon=lon)
            self.ids.map_view.add_marker(marker)
            self.markers.append(marker)
        if points:
            self.route_layer = RouteLayer(points=points)
            self.ids.map_view.add_layer(self.route_layer, mode='window')
            self.ids.map_view.center_on(points[0][0], points[0][1])
            self.ids.map_view.zoom = 12

    def mark_street_done(self, street_id):
        models.mark_street_done(street_id)
        self.load_assignments()

    def compute_route(self):
        coords = [(s['lat'], s['lon']) for s in self.streets if s['lat'] is not None and s['lon'] is not None]
        route = compute_route(coords)
        self.route_text = format_route(route)
        self.update_map(route)


class RootWidget(ScreenManager):
    pass


class MagDistApp(App):
    map_cache_dir = StringProperty('')
    map_source = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_role = ''
        self.current_profile_id = None

    def build(self):
        models.init_db()
        self.map_cache_dir = os.path.join(os.path.dirname(__file__), 'mapcache')
        os.makedirs(self.map_cache_dir, exist_ok=True)
        from kivy_garden.mapview.source import MapSource
        self.map_source = MapSource(
            url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            cache_key='osm',
            min_zoom=0,
            max_zoom=19,
            tile_size=256,
            image_ext='png',
            attribution='© OpenStreetMap contributors',
            subdomains='abc',
        )
        Builder.load_file(KV)
        root = RootWidget()
        root.current = 'login'
        return root

    def login_manager(self):
        self.current_role = 'manager'
        self.current_profile_id = None
        self.root.current = 'manager'

    def login_supervisor(self, supervisor_id):
        self.current_role = 'supervisor'
        self.current_profile_id = supervisor_id
        supervisor_screen = self.root.get_screen('supervisor')
        supervisor_screen.supervisor_id = supervisor_id
        self.root.current = 'supervisor'

    def login_user(self, user_id):
        self.current_role = 'user'
        self.current_profile_id = user_id
        user_screen = self.root.get_screen('user')
        user_screen.user_id = user_id
        self.root.current = 'user'

    def logout(self):
        self.current_role = ''
        self.current_profile_id = None
        self.root.current = 'login'

    # No demo build helper remains. Production flows use explicit supervisor/campaign assignment.


if __name__ == '__main__':
    MagDistApp().run()
