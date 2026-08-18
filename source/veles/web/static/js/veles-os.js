/*
 * =========================================================
 * VELES OS
 * =========================================================
 * Global OS shell only.
 *
 * Translation and theme are handled exclusively by
 * settings.js.
 * =========================================================
 */

(function () {

    "use strict";

    function initialize() {

        const settings = window.VELES_SETTINGS;

        if (!settings) {
            console.error(
                "[VELES OS] VELES_SETTINGS not available."
            );
            return;
        }

        const languageSelect =
            document.getElementById(
                "veles-language-select"
            );

        const themeSelect =
            document.getElementById(
                "veles-theme-select"
            );

        if (languageSelect) {

            languageSelect.value =
                settings.getLanguage();

        }

        if (themeSelect) {

            themeSelect.value =
                settings.getTheme();

        }

        console.log(
            "[VELES OS] Initialized."
        );

    }


    document.addEventListener(
        "DOMContentLoaded",
        initialize
    );


})();
