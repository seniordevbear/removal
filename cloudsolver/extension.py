import os

def proxies(username, password, endpoint, port):
    manifest_json = """
    {
        "manifest_version": 3,
        "name": "Proxies",
        "version": "1.0.0",
        "permissions": [
            "proxy",
            "storage",
            "webRequest",
            "webRequestAuthProvider"
        ],
        "host_permissions": [
            "<all_urls>"
        ],
        "background": {
            "service_worker": "background.js"
        },
        "minimum_chrome_version": "88.0.0",
        "action": {
            "default_title": "Proxies"
        }
    }
    """

    background_js = """
        chrome.runtime.onInstalled.addListener(() => {
            const config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

            chrome.proxy.settings.set(
                { value: config, scope: "regular" },
                function () {
                console.log("Proxy settings applied");
                }
            );
        });

        chrome.webRequest.onAuthRequired.addListener(
            function (details) {
                return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
                };
            },
            { urls: ["<all_urls>"] },
            ["blocking"]
        );

    """ % (endpoint, port, username, password)

    # extension = 'proxies_extension.zip'

    # with zipfile.ZipFile(extension, 'w') as zp:
    #     zp.writestr("manifest.json", manifest_json)
    #     zp.writestr("background.js", background_js)

    # return extension
    
    directory_name = "extension"

    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

    manifest_path = os.path.join(directory_name, "manifest.json")
    background_path = os.path.join(directory_name, "background.js")

    with open(manifest_path, 'w') as manifest_file:
        manifest_file.write(manifest_json)

    with open(background_path, 'w') as background_file:
        background_file.write(background_js)

