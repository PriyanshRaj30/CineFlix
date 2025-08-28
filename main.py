from nicegui import ui, app
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os

from Api.TmdbApi import TmdbAPI
from item_card import item_card
from Models import nav_bar

load_dotenv()

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

tmdb_api = TmdbAPI()

# --------------------- LOGIN PAGE ---------------------
@ui.page('/login')
async def login_page():
    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    
    nav_bar.init_navbar()

    with ui.card().classes('absolute-center w-full sm:w-96 p-4'):
        username = ui.input('Username')
        password = ui.input('Password', password=True)
        
        async def try_login():
            if username.value == USERNAME and password.value == PASSWORD:
                app.storage.user['authenticated'] = True
                next_page = app.storage.user.pop('next', '/')
                ui.navigate.to(next_page)
            else:
                ui.notify('Invalid username or password', type='negative')
        
        ui.button('Login', on_click=try_login).classes("mt-2 w-full")

# --------------------- HOME PAGE ---------------------
@ui.page("/")
async def home_page(page_no: int = 1):
    if not app.storage.user.get('authenticated', False):
        app.storage.user['next'] = str(ui.context.client.request.url)
        return RedirectResponse('/login')
    
    movies = await tmdb_api.discover_movies(page_no=page_no)
    items = movies["items"]

    nav_bar.init_navbar()

    # Search bar responsive
    with ui.row().classes("flex flex-col sm:flex-row gap-2 mb-4"):
        query = ui.input(label="Search Movies").props("rounded outlined dense")
        ui.button(
            icon="search",
            text="Search",
            on_click=lambda x: ui.navigate.to(f"/search?mode=movie&query={query.value}")
        )
    
    # Responsive grid
    with ui.grid().classes("grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"):
        for item in items:
            item_card(
                title=item["title"],
                poster=item["poster"],
                href=item["id"],
                release_date=item["release_date"],
                ratings=item["ratings"],
                adult=item["adult"],
            )
    
    ui.pagination(
        1,
        page_no + 10,
        direction_links=True,
        on_change=lambda x: ui.navigate.to(f"/?page_no={x.value}"),
        value=page_no,
    )

# --------------------- WATCH MOVIE PAGE ---------------------
@ui.page("/watch_movie")
async def watch_movie(tmdb_id):
    if not app.storage.user.get('authenticated', False):
        app.storage.user['next'] = str(ui.context.client.request.url)
        return RedirectResponse('/login')
    
    nav_bar.init_navbar()
    movie_details = await tmdb_api.get_movie_details(tmdb_id)

    ui.image(movie_details["banner"]).classes("w-full h-64 object-cover rounded")

    with ui.grid(columns=1, gap=4, classes="sm:grid-cols-3"):
        ui.image(movie_details["poster"]).props("fit=scale-down").classes("w-full sm:w-auto h-64 mx-auto")
        
        with ui.column().classes("sm:col-span-2"):
            ui.label(movie_details["title"]).classes("text-h5 font-bold")
            ui.label("Description:").classes("text-h6 mt-2")
            ui.label(movie_details["plot"]).classes("text-sm")
            
            ui.label("Casts:").classes("text-h6 mt-2")
            with ui.scroll_area().classes("w-full sm:w-auto h-32"):
                with ui.row().classes("gap-2 overflow-x-auto"):
                    for cast in movie_details["casts"]:
                        with ui.column().classes("w-24"):
                            ui.image(cast["photo"]).classes("w-full h-24 object-cover rounded")
                            ui.label(cast["name"]).classes("text-center text-xs truncate")

    # Responsive video iframe
    with ui.tabs().classes("w-full mt-4") as tabs:
        one = ui.tab("Source 1")
        two = ui.tab("Source 2")
    
    with ui.tab_panels(tabs).classes("w-full"):
        for source, tab in zip(
            [f"https://vidsrc.to/embed/movie/{movie_details['imdb_id']}",
             f"https://vidsrc.xyz/embed/movie/{movie_details['imdb_id']}"],
            [one, two]
        ):
            with ui.tab_panel(tab):
                with ui.element('div').classes('relative w-full pb-[56.25%]'):  # 16:9 aspect
                    ui.html(f"""
                        <iframe
                            src="{source}"
                            class="absolute top-0 left-0 w-full h-full"
                            frameborder="0"
                            allowfullscreen
                            scrolling="no">
                        </iframe>
                    """)

# --------------------- RUN APP ---------------------
ui.run(port=8000, storage_secret=os.getenv('STORAGE_SECRET', 'secret_key'))