self.addEventListener("push", function (event) {

    let data = {
        title: "سجل جديد",
        body: "تمت إضافة سجل جديد إلى لوحة الإدارة."
    };

    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (e) {
        console.log("Push data is not JSON");
    }

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: "/icon-192.png",
            badge: "/icon-192.png",
            dir: "rtl",
            lang: "ar",
            tag: "admin-new-record",
            renotify: true
        })
    );
});