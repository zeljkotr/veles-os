/*
 * =========================================================
 * VELES OS
 * =========================================================
 * Global VELES Desktop UI controller.
 *
 * Responsibilities:
 * - Initialize VELES OS settings
 * - Initialize Desktop navigation
 * - Maintain browser-side Desktop state
 * - Coordinate Desktop UI lifecycle events
 * - Provide a stable browser API for Desktop applications
 *
 * Translation and theme are handled exclusively by
 * settings.js.
 * =========================================================
 */

(function () {

    "use strict";


    /*
     * =====================================================
     * DESKTOP STATE
     * =====================================================
     */

    const desktopState = {

        activeView: "dashboard",

        ready: false

    };


    /*
     * =====================================================
     * DISPATCH DESKTOP EVENT
     * =====================================================
     */

    function dispatchDesktopEvent(
        eventName,
        detail
    ) {

        document.dispatchEvent(
            new CustomEvent(
                eventName,
                {
                    detail: detail || {}
                }
            )
        );

    }


    /*
     * =====================================================
     * SET ACTIVE NAVIGATION ITEM
     * =====================================================
     */

    function setActiveNavigation(
        activeItem
    ) {

        const items =
            document.querySelectorAll(
                ".desktop-navigation-item"
            );


        items.forEach(
            function (item) {

                item.classList.remove(
                    "active"
                );

            }
        );


        if (activeItem) {

            activeItem.classList.add(
                "active"
            );

        }

    }


    /*
     * =====================================================
     * FIND NAVIGATION ITEM
     * =====================================================
     */

    function findNavigationItem(
        view
    ) {

        const items =
            document.querySelectorAll(
                ".desktop-navigation-item"
            );


        for (
            const item of items
        ) {

            if (
                item.dataset.desktopView ===
                view
            ) {

                return item;

            }

        }


        return null;

    }


    /*
     * =====================================================
     * OPEN DESKTOP VIEW
     * =====================================================
     */

    function openDesktopView(
        view
    ) {

        if (!view) {

            return false;

        }


        const previousView =
            desktopState.activeView;


        desktopState.activeView =
            view;


        const navigationItem =
            findNavigationItem(
                view
            );


        setActiveNavigation(
            navigationItem
        );


        console.log(
            "[VELES DESKTOP] Active view:",
            view
        );


        /*
         * -----------------------------------------------
         * VIEW CHANGE EVENT
         * -----------------------------------------------
         */

        dispatchDesktopEvent(
            "veles:desktop:view",
            {
                view: view,

                previousView:
                    previousView
            }
        );


        /*
         * -----------------------------------------------
         * STATE EVENT
         * -----------------------------------------------
         */

        dispatchDesktopEvent(
            "veles:desktop:state",
            {
                state:
                    getDesktopState()
            }
        );


        return true;

    }


    /*
     * =====================================================
     * INITIALIZE DESKTOP NAVIGATION
     * =====================================================
     */

    function initializeDesktopNavigation() {

        const navigationItems =
            document.querySelectorAll(
                ".desktop-navigation-item"
            );


        if (!navigationItems.length) {

            console.log(
                "[VELES DESKTOP] No navigation items found."
            );

            return;

        }


        navigationItems.forEach(
            function (item) {

                item.addEventListener(
                    "click",
                    function (event) {

                        const href =
                            item.getAttribute(
                                "href"
                            );


                        /*
                         * -----------------------------------
                         * DESKTOP APPLICATION VIEW
                         * -----------------------------------
                         *
                         * Placeholder views use "#".
                         * Real Flask routes continue normal
                         * browser navigation.
                         */

                        const view =
                            item.dataset.desktopView;


                        if (
                            view
                            &&
                            (
                                href === "#"
                                ||
                                !href
                            )
                        ) {

                            event.preventDefault();

                            openDesktopView(
                                view
                            );

                            return;

                        }


                        /*
                         * -----------------------------------
                         * REAL APPLICATION ROUTE
                         * -----------------------------------
                         *
                         * Keep normal browser navigation.
                         *
                         * The Desktop navigation state is
                         * updated before leaving the page.
                         */

                        if (view) {

                            setActiveNavigation(
                                item
                            );

                            desktopState.activeView =
                                view;

                        }

                    }
                );

            }
        );


        console.log(
            "[VELES DESKTOP] Navigation initialized."
        );

    }


    /*
     * =====================================================
     * INITIALIZE DESKTOP STATE
     * =====================================================
     */

    function initializeDesktopState() {

        const dashboardItem =
            findNavigationItem(
                "dashboard"
            );


        desktopState.activeView =
            "dashboard";


        setActiveNavigation(
            dashboardItem
        );

    }


    /*
     * =====================================================
     * GET DESKTOP STATE
     * =====================================================
     */

    function getDesktopState() {

        return {

            activeView:
                desktopState.activeView,

            ready:
                desktopState.ready

        };

    }


    /*
     * =====================================================
     * INITIALIZE VELES OS
     * =====================================================
     */

    function initialize() {

        console.log(
            "[VELES OS] Initializing Desktop UI..."
        );


        const settings =
            window.VELES_SETTINGS;


        if (!settings) {

            console.error(
                "[VELES OS] VELES_SETTINGS not available."
            );

            return;

        }


        /*
         * -----------------------------------------------
         * LANGUAGE
         * -----------------------------------------------
         */

        const languageSelect =
            document.getElementById(
                "veles-language-select"
            );


        if (languageSelect) {

            languageSelect.value =
                settings.getLanguage();

        }


        /*
         * -----------------------------------------------
         * THEME
         * -----------------------------------------------
         */

        const themeSelect =
            document.getElementById(
                "veles-theme-select"
            );


        if (themeSelect) {

            themeSelect.value =
                settings.getTheme();

        }


        /*
         * -----------------------------------------------
         * DESKTOP STATE
         * -----------------------------------------------
         */

        initializeDesktopState();


        /*
         * -----------------------------------------------
         * DESKTOP NAVIGATION
         * -----------------------------------------------
         */

        initializeDesktopNavigation();


        /*
         * -----------------------------------------------
         * DESKTOP READY
         * -----------------------------------------------
         */

        desktopState.ready =
            true;


        console.log(
            "[VELES OS] Desktop UI: READY"
        );


        dispatchDesktopEvent(
            "veles:desktop:ready",
            {
                state:
                    getDesktopState()
            }
        );


        dispatchDesktopEvent(
            "veles:desktop:state",
            {
                state:
                    getDesktopState()
            }
        );

    }


    /*
     * =====================================================
     * PUBLIC DESKTOP API
     * =====================================================
     */

    window.VELES_DESKTOP = {

        /*
         * -----------------------------------------------
         * GET ACTIVE VIEW
         * -----------------------------------------------
         */

        getActiveView: function () {

            return desktopState.activeView;

        },


        /*
         * -----------------------------------------------
         * OPEN VIEW
         * -----------------------------------------------
         */

        open: function (
            view
        ) {

            return openDesktopView(
                view
            );

        },


        /*
         * -----------------------------------------------
         * GET STATE
         * -----------------------------------------------
         */

        state: function () {

            return getDesktopState();

        },


        /*
         * -----------------------------------------------
         * READY
         * -----------------------------------------------
         */

        isReady: function () {

            return desktopState.ready;

        }

    };


    /*
     * =====================================================
     * DOM READY
     * =====================================================
     */

    document.addEventListener(
        "DOMContentLoaded",
        initialize
    );


})();