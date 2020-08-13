from bs4 import BeautifulSoup


def parse_summary(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    ret = ""
    summary = soup.find('summary')
    if summary:
        ret = summary.string
    return ret

