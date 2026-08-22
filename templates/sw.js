self.addEventListener("install", function (event) {
    console.log("Service Worker installed");
    self.skipWaiting();
});

self.addEventListener("activate", function (event) {
    console.log("Service Worker activated");

    event.waitUntil(
        self.clients.claim()
    );
});

self.addEventListener("push", function (event) {

    let title = "سجل جديد";
    let body = "تمت إضافة سجل جديد إلى لوحة الإدارة.";

    if (event.data) {
        try {
            const data = event.data.json();

            if (data.title) {
                title = data.title;
            }

            if (data.body) {
                body = data.body;
            }

        } catch (error) {
            console.log("Push data is not JSON");
        }
    }

    event.waitUntil(
        self.registration.showNotification(
            title,
            {
                body: body,
                icon: "/icon-192.png",
                badge: "/icon-192.png",
                dir: "rtl",
                lang: "ar",
                tag: "admin-new-record",
                renotify: true
            }
        )
    );
});

self.addEventListener(
    "notificationclick",
    function (event) {

        event.notification.close();

        event.waitUntil(
            clients.matchAll({
                type: "window",
                includeUncontrolled: true
            }).then(function (clientList) {

                for (const client of clientList) {

                    if (
                        client.url.includes(
                            "snop-login.vercel.app"
                        )
                    ) {
                        return client.focus();
                    }
                }

                if (clients.openWindow) {
                    return clients.openWindow(
                        "https://snop-login.vercel.app/admin"
                    );
                }

            })
        );

    }
);