/*
 * =========================================================
 * VELES SETTINGS
 * =========================================================
 *
 * Single source of truth for:
 *   - Language (i18n) - default: ENGLISH
 *   - Theme (dark/light) - default: DARK
 *   - All translations centralized
 *
 * This is the ONLY translation engine for VELES OS.
 * =========================================================
 */

(function() {

    "use strict";


    // =========================================================
    // CONFIGURATION
    // =========================================================

    var CONFIG = {
        defaultLanguage: 'en',
        supportedLanguages: ['en', 'sr'],
        defaultTheme: 'dark',
        supportedThemes: ['dark', 'light'],
        storageKey: 'veles-settings'
    };


    // =========================================================
    // TRANSLATIONS DICTIONARY
    // =========================================================

    var TRANSLATIONS = {

        // =====================================================
        // ENGLISH
        // =====================================================

        en: {

            // =============================================
            // NAVIGATION
            // =============================================

            'nav.workspace': 'WORKSPACE',
            'nav.overview': 'OVERVIEW',
            'nav.operations': 'OPERATIONS',
            'nav.discovery': 'DISCOVERY',
            'nav.system': 'SYSTEM',
            'nav.events': 'EVENTS',
            'nav.intelligence': 'INTELLIGENCE',
            'nav.ai': 'AI ASSISTANT',
            'nav.memory': 'MEMORY',
            'nav.dashboard': 'DASHBOARD',
            'nav.infrastructure': 'INFRASTRUCTURE',
            'nav.monitoring': 'MONITORING',
            'nav.services': 'SERVICES',
            'nav.logs': 'LOGS',
            'nav.network': 'NETWORK',
            'nav.delivery': 'DELIVERY',
            'nav.security': 'SECURITY',


            // =============================================
            // SYSTEM
            // =============================================

            'system.veles_os': 'VELES OS',
            'system.local_system': 'LOCAL SYSTEM',
            'system.online': '🟢 ONLINE',
            'system.local': '🏠 LOCAL',
            'system.cpu': 'CPU LOAD',
            'system.memory': 'MEMORY',
            'system.disk': 'STORAGE',
            'system.load_average': 'System load average',
            'system.ram_usage': 'RAM usage',
            'system.root_filesystem': 'Root filesystem',
            'system.hostname': 'Hostname',
            'system.os': 'Operating System',
            'system.uptime': 'Uptime',


            // =============================================
            // BRAND
            // =============================================

            'brand.name': 'VELES',
            'brand.os': 'OPERATING SYSTEM',
            'brand.title': 'VELES AI Operations Control Center',


            // =============================================
            // SETTINGS
            // =============================================

            'settings.language': 'LANGUAGE',
            'settings.theme': 'THEME',


            // =============================================
            // LANGUAGES
            // =============================================

            'language.english': 'English',
            'language.serbian': 'Srpski',


            // =============================================
            // DASHBOARD
            // =============================================

            'dashboard.title': 'AI Operations Control Center',
            'dashboard.system_operational': 'SYSTEM OPERATIONAL',
            'dashboard.operations_map': 'OPERATIONS MAP',
            'dashboard.intelligence': 'INTELLIGENCE',
            'dashboard.infrastructure': 'INFRASTRUCTURE',
            'dashboard.delivery': 'DELIVERY',
            'dashboard.core_online': 'CORE ONLINE',
            'dashboard.cloud': 'CLOUD',
            'dashboard.security': 'SECURITY',
            'dashboard.automation': 'AUTOMATION',
            'dashboard.monitoring': 'MONITORING',
            'dashboard.network': 'NETWORK',
            'dashboard.platform': 'PLATFORM',
            'dashboard.data': 'DATA',
            'dashboard.testing': 'TESTING',
            'dashboard.access': 'ACCESS',


            // =============================================
            // MODULES
            // =============================================

            'modules.intelligence': 'INTELLIGENCE',
            'modules.infrastructure': 'INFRASTRUCTURE',
            'modules.delivery': 'DELIVERY',
            'modules.cloud': 'CLOUD',
            'modules.security': 'SECURITY',
            'modules.automation': 'AUTOMATION',
            'modules.monitoring': 'MONITORING',
            'modules.network': 'NETWORK',
            'modules.platform': 'PLATFORM',
            'modules.data': 'DATA',
            'modules.testing': 'TESTING',
            'modules.access': 'ACCESS',


            // =============================================
            // INFRASTRUCTURE
            // =============================================

            'infrastructure.title': 'INFRASTRUCTURE CENTER',
            'infrastructure.subtitle':
                'Veles infrastructure inventory and monitoring',
            'infrastructure.registry': 'RESOURCE REGISTRY',
            'infrastructure.ready': 'INFRASTRUCTURE READY',
            'infrastructure.core_live_status':
                'VELES CORE LIVE STATUS',
            'infrastructure.no_servers':
                'No registered servers.',
            'infrastructure.add_resource':
                'Add Resource',
            'infrastructure.edit_resource':
                'Edit Resource',
            'infrastructure.delete_resource':
                'Delete Resource',
            'infrastructure.resource_details':
                'Resource Details',
            'infrastructure.verify': 'Verify',
            'infrastructure.monitor': 'Monitor',


            // =============================================
            // ACTION
            // =============================================

            'action.add_resource': 'ADD RESOURCE',


            // =============================================
            // RESOURCES
            // =============================================

            'resources.servers': 'SERVERS',
            'resources.containers': 'CONTAINERS',
            'resources.agents': 'AGENTS',
            'resources.devices': 'DEVICES',
            'resources.cloud': 'CLOUD',
            'resources.registered': 'REGISTERED SERVERS',
            'resources.username': 'USERNAME',
            'resources.group': 'GROUP',


            // =============================================
            // DISCOVERY
            // =============================================

            'discovery.active': 'DISCOVERY ACTIVE',
            'discovery.scan': 'DISCOVER',
            'discovery.discovered': 'DISCOVERED HOSTS',


            // =============================================
            // COMMON
            // =============================================

            'common.host': 'HOST',
            'common.port': 'PORT',
            'common.type': 'TYPE',
            'common.found': 'FOUND',


            // =============================================
            // NETWORK
            // =============================================

            'network.title': 'NETWORK',
            'network.subtitle':
                'Network connectivity and system topology',
            'network.overview': 'NETWORK OVERVIEW',
            'network.hostname': 'HOSTNAME',
            'network.interfaces': 'INTERFACES',
            'network.routes': 'ROUTES',
            'network.network_interfaces':
                'NETWORK INTERFACES',
            'network.address': 'IP Address',
            'network.routing_table': 'ROUTING TABLE',
            'network.route': 'ROUTE',
            'network.dns': 'DNS',
            'network.resolver_status': 'RESOLVER STATUS',
            'network.system_dns': 'SYSTEM DNS',
            'network.unavailable': 'Unavailable',


            // =============================================
            // SECURITY
            // =============================================

            'security.title': 'SECURITY CENTER',
            'security.subtitle':
                'Security inspection and system security state',

            'security.active': '🔐 SECURITY ACTIVE',
            'security.read_only': 'READ-ONLY',
            'security.local_inspection': 'LOCAL INSPECTION',

            'security.run_scan': '▶ RUN SECURITY SCAN',

            'security.status': '🛡 SECURITY STATUS',
            'security.checks': 'CHECKS',
            'security.healthy': 'HEALTHY',
            'security.warnings': 'WARNINGS',
            'security.errors': 'ERRORS',
            'security.unknown': 'UNKNOWN',

            'security.not_scanned': 'NOT SCANNED',

            'security.security_checks': '🔎 SECURITY CHECKS',

            'security.target': 'TARGET',
            'security.scope': 'SCOPE',
            'security.host': 'HOST',
            'security.hostname': 'HOSTNAME',
            'security.platform': 'PLATFORM',
            'security.os': 'OS',
            'security.connector': 'CONNECTOR',
            'security.mode': 'MODE',
            'security.timestamp': 'TIMESTAMP',
            'security.message': 'MESSAGE',

            'security.system_inspection':
                'SYSTEM INSPECTION',

            'security.user': 'USER',
            'security.uid': 'UID',
            'security.release': 'RELEASE',
            'security.architecture': 'ARCHITECTURE',

            'security.view_local_users':
                'VIEW {count} LOCAL USERS',

            'security.username': 'USERNAME',
            'security.gid': 'GID',
            'security.home': 'HOME',
            'security.shell': 'SHELL',

            'security.view_privileged_users':
                'VIEW PRIVILEGED USERS',

            'security.reason': 'REASON',

            'security.uid_zero': 'UID 0',

            'security.view_listening_sockets':
                'VIEW LISTENING SOCKETS',

            'security.protocol': 'PROTOCOL',
            'security.state': 'STATE',
            'security.address': 'ADDRESS',
            'security.port': 'PORT',
            'security.process': 'PROCESS',
            'security.pid': 'PID',

            'security.view_running_services':
                'VIEW {count} RUNNING SERVICES',

            'security.service': 'SERVICE',
            'security.running': 'RUNNING',

            'security.ssh_inspection':
                'SSH INSPECTION',

            'security.configuration': 'CONFIGURATION',
            'security.read_only_inspection':
                'READ-ONLY INSPECTION',

            'security.view_firewall_inspection':
                'VIEW FIREWALL INSPECTION',

            'security.inspection': 'INSPECTION',
            'security.return_code': 'RETURN CODE',

            'security.active_status': 'ACTIVE',
            'security.inactive_status': 'INACTIVE',

            'security.view_file_permissions':
                'VIEW {count} FILE PERMISSIONS',

            'security.path': 'PATH',
            'security.exists': 'EXISTS',
            'security.mode_value': 'MODE',
            'security.permissions': 'PERMISSIONS',
            'security.owner': 'OWNER',
            'security.group': 'GROUP',
            'security.expected': 'EXPECTED',

            'security.view_details':
                'VIEW DETAILS',

            'security.scan_not_executed':
                '⚠ SECURITY SCAN HAS NOT BEEN EXECUTED YET.',

            'security.system_security_context':
                '🖥 SYSTEM SECURITY CONTEXT',

            'security.unknown_value': 'UNKNOWN',
            'security.not_available': '—',


            // =============================================
            // STATUS
            // =============================================

            'status.registered': 'registered',
            'status.active': 'active',
            'status.inactive': 'inactive',
            'status.online': 'online',
            'status.offline': 'offline',
            'status.planned': 'planned',
            'status.operational': 'operational',
            'status.failed': 'failed',
            'status.success': 'success',
            'status.pending': 'pending',
            'status.running': 'running',
            'status.stopped': 'stopped',
            'status.enabled': 'enabled',
            'status.disabled': 'disabled',
            'status.unknown': 'unknown',
            'status.core_online': 'CORE ONLINE',


            // =============================================
            // GROUPS
            // =============================================

            'group.network': 'network',
            'group.default': 'default',
            'group.cloud': 'cloud',
            'group.servers': 'servers',
            'group.containers': 'containers',
            'group.agents': 'agents',
            'group.devices': 'devices',


            // =============================================
            // THEME
            // =============================================

            'theme.dark': 'Dark',
            'theme.light': 'Light',
            'theme.select': 'Theme'

        },


        // =====================================================
        // SERBIAN
        // =====================================================

        sr: {

            // =============================================
            // NAVIGACIJA
            // =============================================

            'nav.workspace': 'RADNI PROSTOR',
            'nav.overview': 'PREGLED',
            'nav.operations': 'OPERACIJE',
            'nav.discovery': 'OTKRIVANJE',
            'nav.system': 'SISTEM',
            'nav.events': 'DOGAĐAJI',
            'nav.intelligence': 'INTELIGENCIJA',
            'nav.ai': 'AI ASISTENT',
            'nav.memory': 'MEMORIJA',
            'nav.dashboard': 'KOMANDNA TABLA',
            'nav.infrastructure': 'INFRASTRUKTURA',
            'nav.monitoring': 'MONITORING',
            'nav.services': 'USLUGE',
            'nav.logs': 'DNEVNICI',
            'nav.network': 'MREŽA',
            'nav.delivery': 'DOSTAVA',
            'nav.security': 'BEZBEDNOST',


            // =============================================
            // SISTEM
            // =============================================

            'system.veles_os': 'VELES OS',
            'system.local_system': 'LOKALNI SISTEM',
            'system.online': '🟢 ONLINE',
            'system.local': '🏠 LOKALNO',
            'system.cpu': 'CPU OPTEREĆENJE',
            'system.memory': 'MEMORIJA',
            'system.disk': 'SKLADIŠTE',
            'system.load_average':
                'Prosečno opterećenje sistema',
            'system.ram_usage': 'Upotreba RAM-a',
            'system.root_filesystem':
                'Root sistem datoteka',
            'system.hostname': 'Ime hosta',
            'system.os': 'Operativni sistem',
            'system.uptime': 'Vreme rada',


            // =============================================
            // BREND
            // =============================================

            'brand.name': 'VELES',
            'brand.os': 'OPERATIVNI SISTEM',
            'brand.title':
                'VELES AI Operativni Kontrolni Centar',


            // =============================================
            // POSTAVKE
            // =============================================

            'settings.language': 'JEZIK',
            'settings.theme': 'TEMA',


            // =============================================
            // JEZICI
            // =============================================

            'language.english': 'Engleski',
            'language.serbian': 'Srpski',


            // =============================================
            // DASHBOARD
            // =============================================

            'dashboard.title':
                'AI Operativni Kontrolni Centar',
            'dashboard.system_operational':
                'SISTEM OPERATIVAN',
            'dashboard.operations_map':
                'MAPA OPERACIJA',
            'dashboard.intelligence':
                'INTELIGENCIJA',
            'dashboard.infrastructure':
                'INFRASTRUKTURA',
            'dashboard.delivery':
                'DOSTAVA',
            'dashboard.core_online':
                'CORE ONLINE',
            'dashboard.cloud':
                'OBLAK',
            'dashboard.security':
                'BEZBEDNOST',
            'dashboard.automation':
                'AUTOMATIZACIJA',
            'dashboard.monitoring':
                'MONITORING',
            'dashboard.network':
                'MREŽA',
            'dashboard.platform':
                'PLATFORMA',
            'dashboard.data':
                'PODACI',
            'dashboard.testing':
                'TESTIRANJE',
            'dashboard.access':
                'PRISTUP',


            // =============================================
            // MODULI
            // =============================================

            'modules.intelligence':
                'INTELIGENCIJA',
            'modules.infrastructure':
                'INFRASTRUKTURA',
            'modules.delivery':
                'DOSTAVA',
            'modules.cloud':
                'OBLAK',
            'modules.security':
                'BEZBEDNOST',
            'modules.automation':
                'AUTOMATIZACIJA',
            'modules.monitoring':
                'MONITORING',
            'modules.network':
                'MREŽA',
            'modules.platform':
                'PLATFORMA',
            'modules.data':
                'PODACI',
            'modules.testing':
                'TESTIRANJE',
            'modules.access':
                'PRISTUP',


            // =============================================
            // INFRASTRUKTURA
            // =============================================

            'infrastructure.title':
                'CENTAR INFRASTRUKTURE',
            'infrastructure.subtitle':
                'Veles inventar i monitoring infrastrukture',
            'infrastructure.registry':
                'REGISTAR RESURSA',
            'infrastructure.ready':
                'INFRASTRUKTURA SPREMNA',
            'infrastructure.core_live_status':
                'VELES CORE STATUS UŽIVO',
            'infrastructure.no_servers':
                'Nema registrovanih servera.',
            'infrastructure.add_resource':
                'Dodaj resurs',
            'infrastructure.edit_resource':
                'Izmeni resurs',
            'infrastructure.delete_resource':
                'Obriši resurs',
            'infrastructure.resource_details':
                'Detalji resursa',
            'infrastructure.verify':
                'Proveri',
            'infrastructure.monitor':
                'Monitor',


            // =============================================
            // AKCIJE
            // =============================================

            'action.add_resource':
                'DODAJ RESURS',


            // =============================================
            // RESURSI
            // =============================================

            'resources.servers':
                'SERVERI',
            'resources.containers':
                'KONTEJNERI',
            'resources.agents':
                'AGENTI',
            'resources.devices':
                'UREĐAJI',
            'resources.cloud':
                'OBLAK',
            'resources.registered':
                'REGISTROVANI SERVERI',
            'resources.username':
                'KORISNIČKO IME',
            'resources.group':
                'GRUPA',


            // =============================================
            // DISCOVERY
            // =============================================

            'discovery.active':
                'OTKRIVANJE AKTIVNO',
            'discovery.scan':
                'OTKRIJ',
            'discovery.discovered':
                'OTKRIVENI HOSTOVI',


            // =============================================
            // ZAJEDNIČKO
            // =============================================

            'common.host':
                'HOST',
            'common.port':
                'PORT',
            'common.type':
                'TIP',
            'common.found':
                'PRONAĐEN',


            // =============================================
            // MREŽA
            // =============================================

            'network.title':
                'MREŽA',
            'network.subtitle':
                'Mrežna povezanost i sistemska topologija',
            'network.overview':
                'PREGLED MREŽE',
            'network.hostname':
                'IME HOSTA',
            'network.interfaces':
                'INTERFEJSA',
            'network.routes':
                'RUTE',
            'network.network_interfaces':
                'MREŽNI INTERFEJSI',
            'network.address':
                'IP Adresa',
            'network.routing_table':
                'TABELA RUTIRANJA',
            'network.route':
                'RUTA',
            'network.dns':
                'DNS',
            'network.resolver_status':
                'STATUS DNS REZOLVERA',
            'network.system_dns':
                'SISTEMSKI DNS',
            'network.unavailable':
                'Nedostupno',


            // =============================================
            // BEZBEDNOST
            // =============================================

            'security.title':
                'CENTAR BEZBEDNOSTI',
            'security.subtitle':
                'Bezbednosna inspekcija i stanje bezbednosti sistema',

            'security.active':
                '🔐 BEZBEDNOST AKTIVNA',
            'security.read_only':
                'SAMO ZA ČITANJE',
            'security.local_inspection':
                'LOKALNA INSPEKCIJA',

            'security.run_scan':
                '▶ POKRENI BEZBEDNOSNO SKENIRANJE',

            'security.status':
                '🛡 STATUS BEZBEDNOSTI',
            'security.checks':
                'PROVERE',
            'security.healthy':
                'ISPRAVNO',
            'security.warnings':
                'UPOZORENJA',
            'security.errors':
                'GREŠKE',
            'security.unknown':
                'NEPOZNATO',

            'security.not_scanned':
                'NIJE SKENIRANO',

            'security.security_checks':
                '🔎 BEZBEDNOSNE PROVERE',

            'security.target':
                'CILJ',
            'security.scope':
                'OPSEG',
            'security.host':
                'HOST',
            'security.hostname':
                'IME HOSTA',
            'security.platform':
                'PLATFORMA',
            'security.os':
                'OS',
            'security.connector':
                'KONEKTOR',
            'security.mode':
                'REŽIM',
            'security.timestamp':
                'VREMENSKA OZNAKA',
            'security.message':
                'PORUKA',

            'security.system_inspection':
                'SISTEMSKA INSPEKCIJA',

            'security.user':
                'KORISNIK',
            'security.uid':
                'UID',
            'security.release':
                'IZDANJE',
            'security.architecture':
                'ARHITEKTURA',

            'security.view_local_users':
                'PRIKAŽI {count} LOKALNIH KORISNIKA',

            'security.username':
                'KORISNIČKO IME',
            'security.gid':
                'GID',
            'security.home':
                'MATIČNI DIREKTORIJUM',
            'security.shell':
                'SHELL',

            'security.view_privileged_users':
                'PRIKAŽI PRIVILEGOVANE KORISNIKE',

            'security.reason':
                'RAZLOG',

            'security.uid_zero':
                'UID 0',

            'security.view_listening_sockets':
                'PRIKAŽI OTVORENE SOCKETE',

            'security.protocol':
                'PROTOKOL',
            'security.state':
                'STANJE',
            'security.address':
                'ADRESA',
            'security.port':
                'PORT',
            'security.process':
                'PROCES',
            'security.pid':
                'PID',

            'security.view_running_services':
                'PRIKAŽI {count} POKRENUTIH USLUGA',

            'security.service':
                'USLUGA',
            'security.running':
                'POKRENUTO',

            'security.ssh_inspection':
                'SSH INSPEKCIJA',

            'security.configuration':
                'KONFIGURACIJA',
            'security.read_only_inspection':
                'INSPEKCIJA SAMO ZA ČITANJE',

            'security.view_firewall_inspection':
                'PRIKAŽI FIREWALL INSPEKCIJU',

            'security.inspection':
                'INSPEKCIJA',
            'security.return_code':
                'POVRATNI KOD',

            'security.active_status':
                'AKTIVAN',
            'security.inactive_status':
                'NEAKTIVAN',

            'security.view_file_permissions':
                'PRIKAŽI {count} DOZVOLA DATOTEKA',

            'security.path':
                'PUTANJA',
            'security.exists':
                'POSTOJI',
            'security.mode_value':
                'REŽIM',
            'security.permissions':
                'DOZVOLE',
            'security.owner':
                'VLASNIK',
            'security.group':
                'GRUPA',
            'security.expected':
                'OČEKIVANO',

            'security.view_details':
                'PRIKAŽI DETALJE',

            'security.scan_not_executed':
                '⚠ BEZBEDNOSNO SKENIRANJE JOŠ NIJE IZVRŠENO.',

            'security.system_security_context':
                '🖥 KONTEKST BEZBEDNOSTI SISTEMA',

            'security.unknown_value':
                'NEPOZNATO',
            'security.not_available':
                '—',


            // =============================================
            // STATUS
            // =============================================

            'status.registered':
                'registrovan',
            'status.active':
                'aktivan',
            'status.inactive':
                'neaktivan',
            'status.online':
                'online',
            'status.offline':
                'offline',
            'status.planned':
                'planirano',
            'status.operational':
                'operativan',
            'status.failed':
                'neuspešno',
            'status.success':
                'uspešno',
            'status.pending':
                'na čekanju',
            'status.running':
                'pokrenut',
            'status.stopped':
                'zaustavljen',
            'status.enabled':
                'omogućen',
            'status.disabled':
                'onemogućen',
            'status.unknown':
                'nepoznat',
            'status.core_online':
                'CORE ONLINE',


            // =============================================
            // GRUPE
            // =============================================

            'group.network':
                'mreža',
            'group.default':
                'podrazumevano',
            'group.cloud':
                'oblak',
            'group.servers':
                'serveri',
            'group.containers':
                'kontejneri',
            'group.agents':
                'agenti',
            'group.devices':
                'uređaji',


            // =============================================
            // TEMA
            // =============================================

            'theme.dark':
                'Tamna',
            'theme.light':
                'Svetla',
            'theme.select':
                'Tema'

        }

    };


    // =========================================================
    // TRANSLATION ENGINE
    // =========================================================

    function applyTranslation(language) {

        var lang =
            language || CONFIG.defaultLanguage;


        if (
            CONFIG.supportedLanguages.indexOf(lang) === -1
        ) {

            lang =
                CONFIG.defaultLanguage;

        }


        console.log(
            '[settings.js] Applying language:',
            lang
        );


        document.documentElement.dataset.language =
            lang;


        var elements =
            document.querySelectorAll(
                '[data-i18n]'
            );


        console.log(
            '[settings.js] Elements to translate:',
            elements.length
        );


        elements.forEach(function(element) {

            var key =
                element.getAttribute(
                    'data-i18n'
                );


            var translation = null;


            if (
                TRANSLATIONS[lang] &&
                TRANSLATIONS[lang][key] !== undefined
            ) {

                translation =
                    TRANSLATIONS[lang][key];

            } else if (
                TRANSLATIONS.en &&
                TRANSLATIONS.en[key] !== undefined
            ) {

                translation =
                    TRANSLATIONS.en[key];

            }


            if (translation === null) {
                return;
            }


            console.log(
                '[settings.js] Translating:',
                key,
                '->',
                translation
            );


            if (
                element.children &&
                element.children.length > 0
            ) {

                var childNodes =
                    element.childNodes;

                var translated = false;


                for (
                    var i = 0;
                    i < childNodes.length;
                    i++
                ) {

                    var node =
                        childNodes[i];


                    if (
                        node.nodeType === 3 &&
                        node.textContent.trim() !== ''
                    ) {

                        node.textContent =
                            translation;

                        translated = true;

                        break;

                    }

                }


                if (!translated) {

                    element.textContent =
                        translation;

                }


            } else {

                element.textContent =
                    translation;

            }

        });


        var selector =
            document.getElementById(
                'veles-language-select'
            );


        if (selector) {

            selector.value =
                lang;

        }


        console.log(
            '[settings.js] Translation complete!'
        );

    }


    // =========================================================
    // THEME ENGINE
    // =========================================================

    function applyTheme(theme) {

        var themeValue =
            theme || CONFIG.defaultTheme;


        if (
            CONFIG.supportedThemes.indexOf(themeValue) === -1
        ) {

            themeValue =
                CONFIG.defaultTheme;

        }


        console.log(
            '[settings.js] Applying theme:',
            themeValue
        );


        document.documentElement.dataset.theme =
            themeValue;


        if (document.body) {

            document.body.classList.remove(
                'theme-dark',
                'theme-light'
            );

            document.body.classList.add(
                'theme-' + themeValue
            );

        }


        var selector =
            document.getElementById(
                'veles-theme-select'
            );


        if (selector) {

            selector.value =
                themeValue;

        }


        console.log(
            '[settings.js] Theme applied!'
        );

    }


    // =========================================================
    // GLOBAL API
    // =========================================================

    window.VELES_SETTINGS = {

        getLanguage: function() {

            var language =
                localStorage.getItem(
                    'veles-language'
                );


            if (
                CONFIG.supportedLanguages.indexOf(
                    language
                ) === -1
            ) {

                return CONFIG.defaultLanguage;

            }


            return language;

        },


        setLanguage: function(language) {

            if (
                CONFIG.supportedLanguages.indexOf(
                    language
                ) === -1
            ) {

                language =
                    CONFIG.defaultLanguage;

            }


            localStorage.setItem(
                'veles-language',
                language
            );


            applyTranslation(language);


            window.dispatchEvent(
                new CustomEvent(
                    'veles:language-changed',
                    {
                        detail: {
                            language: language
                        }
                    }
                )
            );

        },


        getTheme: function() {

            var theme =
                localStorage.getItem(
                    'veles-theme'
                );


            if (
                CONFIG.supportedThemes.indexOf(
                    theme
                ) === -1
            ) {

                return CONFIG.defaultTheme;

            }


            return theme;

        },


        setTheme: function(theme) {

            if (
                CONFIG.supportedThemes.indexOf(
                    theme
                ) === -1
            ) {

                theme =
                    CONFIG.defaultTheme;

            }


            localStorage.setItem(
                'veles-theme',
                theme
            );


            applyTheme(theme);


            window.dispatchEvent(
                new CustomEvent(
                    'veles:theme-changed',
                    {
                        detail: {
                            theme: theme
                        }
                    }
                )
            );

        },


        applyLanguage: function(language) {

            applyTranslation(
                language ||
                this.getLanguage()
            );

        },


        applyTheme: function(theme) {

            applyTheme(
                theme ||
                this.getTheme()
            );

        }

    };


    // =========================================================
    // GLOBAL TRANSLATION DICTIONARY
    // =========================================================

    window.VELES_TRANSLATIONS =
        TRANSLATIONS;


    // =========================================================
    // INITIALIZATION
    // =========================================================

    function initialize() {

        console.log(
            '[settings.js] Initializing...'
        );


        var lang =
            window.VELES_SETTINGS.getLanguage();


        var theme =
            window.VELES_SETTINGS.getTheme();


        window.VELES_SETTINGS.applyLanguage(
            lang
        );


        window.VELES_SETTINGS.applyTheme(
            theme
        );


        console.log(
            '[settings.js] Initialized with:',
            {
                language: lang,
                theme: theme
            }
        );

    }


    // =========================================================
    // SELECTORS
    // =========================================================

    function setupSelectors() {

        var languageSelector =
            document.getElementById(
                'veles-language-select'
            );


        if (languageSelector) {

            languageSelector.addEventListener(
                'change',
                function() {

                    window.VELES_SETTINGS.setLanguage(
                        this.value
                    );

                }
            );

        }


        var themeSelector =
            document.getElementById(
                'veles-theme-select'
            );


        if (themeSelector) {

            themeSelector.addEventListener(
                'change',
                function() {

                    window.VELES_SETTINGS.setTheme(
                        this.value
                    );

                }
            );

        }

    }


    // =========================================================
    // DYNAMIC DOM
    // =========================================================

    function observeDOM() {

        if (!window.MutationObserver) {

            console.warn(
                '[settings.js] MutationObserver not available.'
            );

            return;

        }


        var observer =
            new MutationObserver(
                function(mutations) {

                    var hasNewI18nElements =
                        false;


                    mutations.forEach(
                        function(mutation) {

                            if (
                                mutation.type !==
                                'childList'
                            ) {

                                return;

                            }


                            mutation.addedNodes.forEach(
                                function(node) {

                                    if (
                                        node.nodeType !== 1
                                    ) {

                                        return;

                                    }


                                    if (
                                        node.hasAttribute &&
                                        node.hasAttribute(
                                            'data-i18n'
                                        )
                                    ) {

                                        hasNewI18nElements =
                                            true;

                                        return;

                                    }


                                    if (
                                        node.querySelector &&
                                        node.querySelector(
                                            '[data-i18n]'
                                        )
                                    ) {

                                        hasNewI18nElements =
                                            true;

                                    }

                                }
                            );

                        }
                    );


                    if (hasNewI18nElements) {

                        window.VELES_SETTINGS.applyLanguage(
                            window.VELES_SETTINGS.getLanguage()
                        );

                    }

                }
            );


        observer.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );

    }


    // =========================================================
    // BOOT
    // =========================================================

    function boot() {

        setupSelectors();

        initialize();

        observeDOM();

    }


    // =========================================================
    // DOM READY
    // =========================================================

    if (
        document.readyState === 'loading'
    ) {

        document.addEventListener(
            'DOMContentLoaded',
            boot
        );

    } else {

        boot();

    }


})();