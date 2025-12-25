"""Dzen browser automation."""

from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from utils.logger import get_logger
from config.defaults import SESSIONS_DIR, DZEN_BROWSER_TIMEOUT

logger = get_logger(__name__)


class DzenBrowser:
    """Browser automation for Dzen."""
    
    def __init__(self, session_dir: Optional[Path] = None):
        self.session_dir = session_dir or (SESSIONS_DIR / "dzen")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.logger = logger
        self.authenticated = False
    
    async def start(self):
        """Start browser."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with user data dir
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir),
                headless=False,  # Show browser for authentication
                viewport={"width": 1920, "height": 1080},
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # Get first page or create new
            pages = self.browser.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.browser.new_page()
            
            self.context = self.browser  # persistent context acts as context
            
            self.logger.info("Dzen browser started")
        except Exception as e:
            self.logger.error(f"Error starting browser: {e}")
            raise
    
    async def stop(self):
        """Stop browser."""
        try:
            # For persistent context, browser IS the context
            # Just close the browser (context)
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.page = None
            self.context = None
            self.browser = None
            self.authenticated = False
            
            self.logger.info("Dzen browser stopped")
        except Exception as e:
            self.logger.error(f"Error stopping browser: {e}")
    
    async def check_authenticated(self) -> bool:
        """Check if user is authenticated."""
        # For persistent context, browser IS the context
        if not self.browser or not self.page:
            return False
        
        try:
            await self.page.goto("https://dzen.ru", wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(2)  # Wait for page load
            
            # Check for login button (not authenticated) or user menu (authenticated)
            login_button = await self.page.query_selector('a[href*="auth"]')
            user_menu = await self.page.query_selector('[data-testid="user-menu"]')
            
            is_auth = user_menu is not None or login_button is None
            self.authenticated = is_auth
            
            return is_auth
        except Exception as e:
            self.logger.error(f"Error checking authentication: {e}")
            return False
    
    async def wait_for_authentication(self, timeout: int = 300):
        """Wait for user to authenticate manually."""
        if not self.browser or not self.page:
            raise RuntimeError("Browser not started")
        
        self.logger.info("Waiting for manual authentication...")
        await self.page.goto("https://id.yandex.ru/auth", wait_until="domcontentloaded")
        
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if await self.check_authenticated():
                self.logger.info("Authentication successful")
                return True
            await asyncio.sleep(2)
        
        return False
    
    async def create_article(
        self,
        title: str,
        content: str,
        tags: Optional[list[str]] = None,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create and publish article on Dzen."""
        if not self.browser or not self.page:
            raise RuntimeError("Browser not started")
        
        if not self.authenticated:
            if not await self.check_authenticated():
                raise RuntimeError("Not authenticated")
        
        try:
            # Navigate to editor
            await self.page.goto("https://zen.yandex.ru/editor", wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Wait for editor to load
            
            # Fill title
            title_selector = 'input[placeholder*="заголовок"], input[data-testid*="title"]'
            title_input = await self.page.wait_for_selector(title_selector, timeout=10000)
            await title_input.fill(title)
            await asyncio.sleep(1)
            
            # Upload image if provided (BEFORE content to insert it properly)
            if image_path and Path(image_path).exists():
                try:
                    await asyncio.sleep(1)
                    # Look for image upload
                    file_inputs = await self.page.query_selector_all('input[type="file"]')
                    for file_input in file_inputs:
                        try:
                            await file_input.set_input_files(str(image_path))
                            await asyncio.sleep(3)
                            self.logger.info(f"Image uploaded: {image_path}")
                            break
                        except:
                            continue
                except Exception as e:
                    self.logger.warning(f"Could not upload image: {e}")
            
            # Fill content
            content_selector = 'div[contenteditable="true"], textarea[placeholder*="текст"]'
            content_input = await self.page.wait_for_selector(content_selector, timeout=10000)
            await content_input.fill(content)
            await asyncio.sleep(1)
            
            # Add tags if provided
            if tags:
                tags_selector = 'input[placeholder*="тег"], input[data-testid*="tag"]'
                tags_input = await self.page.query_selector(tags_selector)
                if tags_input:
                    for tag in tags[:5]:  # Max 5 tags
                        await tags_input.fill(tag)
                        await tags_input.press("Enter")
                        await asyncio.sleep(0.5)
            
            # Publish button
            publish_selector = 'button:has-text("Опубликовать"), button[data-testid*="publish"]'
            publish_button = await self.page.wait_for_selector(publish_selector, timeout=10000)
            await publish_button.click()
            await asyncio.sleep(3)  # Wait for publication
            
            # Get article URL from page
            current_url = self.page.url
            article_id = current_url.split('/')[-1] if '/' in current_url else None
            
            self.logger.info(f"Article published on Dzen: {article_id}")
            
            return {
                "success": True,
                "article_id": article_id,
                "url": current_url
            }
        except Exception as e:
            self.logger.error(f"Error creating article: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Get browser status."""
        return {
            "browser_running": self.browser is not None,
            "authenticated": self.authenticated,
            "session_dir": str(self.session_dir)
        }

