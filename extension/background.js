
        chrome.runtime.onInstalled.addListener(() => {
            const config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "isp.smartproxy.com",
                    port: parseInt(10002)
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
                    username: "sp1vj8y5du",
                    password: "o2ajgcB~6lLHMc22ep"
                }
                };
            },
            { urls: ["<all_urls>"] },
            ["blocking"]
        );

    