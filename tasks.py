from pathlib import Path

from robocorp.tasks import task
from robocorp import browser

from RPA.Archive import Archive
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Tables import Tables


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(slowmo=100)
    open_robot_order_website()
    orders = get_orders()
    for row in orders:
        close_annoying_model()
        fill_the_form(row)
        preview_robot()
        submit_order()
        order_number = row["Order number"]
        pdf_file = store_receipt_as_pdf(order_number)
        screenshot = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot, pdf_file)
        order_another_robot()
    archive_receipts()


def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    http = HTTP()
    http.download(
        url="https://robotsparebinindustries.com/orders.csv",
        overwrite=True,
    )
    library = Tables()
    return library.read_table_from_csv("orders.csv", header=True)


def close_annoying_model():
    page = browser.page()
    page.click("button:text('OK')")


def fill_the_form(row):
    page = browser.page()
    page.select_option("#head", row["Head"])
    page.check(f"#id-body-{row['Body']}")
    # The legs input's id changes, so target it by its placeholder text instead
    page.fill("input[placeholder='Enter the part number for the legs']", row["Legs"])
    page.fill("#address", row["Address"])


def preview_robot():
    page = browser.page()
    page.click("#preview")


def submit_order():
    page = browser.page()
    while True:
        page.click("#order")
        # Wait until either the receipt or the error message appears
        page.wait_for_selector("#receipt, .alert-danger")
        if page.is_visible("#receipt"):
            break  # success
        # Otherwise there was an error, so the loop clicks Order again


def store_receipt_as_pdf(order_number):
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    Path("output/receipts").mkdir(parents=True, exist_ok=True)
    pdf_path = f"output/receipts/receipt_{order_number}.pdf"

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, pdf_path)
    return pdf_path


def screenshot_robot(order_number):
    page = browser.page()

    Path("output/screenshots").mkdir(parents=True, exist_ok=True)
    screenshot_path = f"output/screenshots/robot_{order_number}.png"

    page.locator("#robot-preview-image").screenshot(path=screenshot_path)
    return screenshot_path


def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True,
    )


def order_another_robot():
    page = browser.page()
    page.click("#order-another")


def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip("output/receipts", "output/receipts.zip")