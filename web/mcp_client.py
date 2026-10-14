from mcp_servers.will_it_burn.server import get_MCP_url as get_will_it_burn_MCP_url
from mcp_servers.variety_classifier.server import get_MCP_url as get_variety_classifier_MCP_url


def get_MCP_urls():
    return [
        get_will_it_burn_MCP_url(),
        get_variety_classifier_MCP_url(),
    ]


if __name__ == "__main__":
    for url in get_MCP_urls():
        print(url)