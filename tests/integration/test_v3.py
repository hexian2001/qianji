import asyncio
import os
import sys

from playwright.async_api import async_playwright

from qianji.core.pw_client import PlaywrightClient

# 获取当前文件目录下的 fixture 路径
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
TEST_HTML = f"file://{os.path.abspath(os.path.join(FIXTURE_DIR, 'v3_test.html'))}"


async def test_full_v3_capabilities():
    print("Starting V3 Integration Test...")
    async with async_playwright() as p:
        print("Launching browser with --no-sandbox...")
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        try:
            client = PlaywrightClient()

            # 1. 导航与快照 (Cap 1, 4, 5)
            print(f"Navigating to {TEST_HTML}...")
            await client.navigate(page, TEST_HTML)
            print("Creating snapshot...")
            snapshot = await client.create_snapshot(page, max_elements=100)

            # 验证 iframe 提取 (Cap 1)
            print("Verifying iframe extraction...")
            iframe_elements = [e for e in snapshot.elements.values() if e.frame_id]
            print(f"Found {len(iframe_elements)} elements in iframe")
            assert len(iframe_elements) > 0, "Should extract elements from iframe"

            iframe_btn = next((e for e in iframe_elements if e.name == "Iframe Button"), None)
            assert iframe_btn is not None
            assert iframe_btn.frame_id == "f1"
            print("✓ Iframe extraction verified")

            # 验证裁剪 (Cap 5)
            print(f"Verifying truncation: {len(snapshot.elements)}/{snapshot.total_elements_found}")
            assert len(snapshot.elements) <= 100
            assert snapshot.total_elements_found > 200
            print("✓ Truncation verified")

            # 验证 DOM Hash (Cap 4)
            print("Verifying DOM Hash...")
            old_hash = snapshot.dom_hash
            assert old_hash != ""
            await page.click("#change-dom-btn")
            await asyncio.sleep(0.5)
            current_hash = await page.evaluate(
                "() => `${location.href}|${document.querySelectorAll('a,button,input,select,textarea,[role]').length}|${document.body.innerText.length}`"
            )
            assert old_hash != current_hash
            print("✓ DOM Hash change detected")

            # 2. 弹窗处理 (Cap 2)
            print("Verifying Dialog handling...")
            client.set_dialog_mode("accept")
            alert_ref = next(e.ref for e in snapshot.elements.values() if e.name == "Trigger Alert")
            await client.click_by_ref(page, alert_ref, snapshot)

            history = client.get_dialog_history()
            assert len(history) > 0
            assert history[-1]["message"] == "Hello from Alert"
            print(f"✓ Dialog verified: {history[-1]['message']}")

            # 3. Iframe 交互 (Cap 1)
            print("Verifying Iframe interaction...")
            iframe_btn_ref = next(
                e.ref for e in snapshot.elements.values() if e.name == "Iframe Button"
            )
            await client.click_by_ref(page, iframe_btn_ref, snapshot)

            content = await client.get_text_by_ref(page, iframe_btn_ref, snapshot)
            assert content == "Iframe Clicked"
            print("✓ Iframe interaction verified")

            # 4. 标注截图 (Cap 6)
            print("Verifying Annotated Screenshot...")
            temp_img = "/tmp/annotated_test.png"
            await client.annotated_screenshot(page, temp_img, snapshot)
            assert os.path.exists(temp_img)
            assert os.path.getsize(temp_img) > 0
            print(f"✓ Annotated screenshot saved to {temp_img}")

            print("\nALL V3 INTEGRATION TESTS PASSED! ✅")

        except Exception as e:
            print(f"\nTEST FAILED: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_full_v3_capabilities())
