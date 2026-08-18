document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById(
                "chat-form"
            );

        const textarea =
            document.getElementById(
                "question"
            );

        const newChatButton =
            document.getElementById(
                "new-chat-button"
            );

        const voiceButton =
            document.getElementById(
                "voice-button"
            );

        const overlay =
            document.getElementById(
                "thinking-overlay"
            );


        /*
        ==========================================
        ENTER = SEND
        SHIFT + ENTER = NOVI RED
        ==========================================
        */

        if (textarea && form) {

            textarea.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {

                        event.preventDefault();

                        form.requestSubmit();

                    }

                }
            );

        }


        /*
        ==========================================
        SUBMIT
        ==========================================
        */

        if (form) {

            form.addEventListener(
                "submit",
                function () {

                    if (overlay) {

                        overlay.style.display =
                            "flex";

                    }

                }
            );

        }


        /*
        ==========================================
        NOVI RAZGOVOR
        ==========================================
        */

        if (newChatButton) {

            newChatButton.addEventListener(
                "click",
                function () {

                    window.location.href =
                        "/chat?new=1";

                }
            );

        }


        /*
        ==========================================
        VELES VOICE
        ==========================================
        */

        if (voiceButton) {

            const SpeechRecognition =
                window.SpeechRecognition ||
                window.webkitSpeechRecognition;


            if (!SpeechRecognition) {

                voiceButton.addEventListener(
                    "click",
                    function () {

                        alert(
                            "Voice input nije podržan u ovom browseru."
                        );

                    }
                );

                return;

            }


            const recognition =
                new SpeechRecognition();


            recognition.lang =
                "sr-RS";


            recognition.continuous =
                false;


            recognition.interimResults =
                false;


            /*
            ======================================
            VOICE START
            ======================================
            */

            voiceButton.addEventListener(
                "click",
                function () {

                    try {

                        recognition.start();

                        voiceButton.innerHTML =
                            "🔴 Slušam...";

                        voiceButton.classList.add(
                            "voice-active"
                        );

                    }

                    catch (error) {

                        console.error(
                            "VOICE START ERROR:",
                            error
                        );

                    }

                }
            );


            /*
            ======================================
            RESULT
            ======================================
            */

            recognition.addEventListener(
                "result",
                function (event) {

                    const result =
                        event.results[0][0];


                    const text =
                        result.transcript.trim();


                    console.log(
                        "VELES VOICE:",
                        text
                    );


                    if (!text) {

                        return;

                    }


                    /*
                    ==============================
                    UBACI PREPOZNATI GOVOR
                    ==============================
                    */

                    if (textarea) {

                        textarea.value =
                            text;

                    }


                    /*
                    ==============================
                    AUTOMATSKI POŠALJI
                    ==============================
                    */

                    if (form) {

                        form.requestSubmit();

                    }

                }
            );


            /*
            ======================================
            VOICE END
            ======================================
            */

            recognition.addEventListener(
                "end",
                function () {

                    voiceButton.innerHTML =
                        "🎤 Veles";

                    voiceButton.classList.remove(
                        "voice-active"
                    );

                }
            );


            /*
            ======================================
            VOICE ERROR
            ======================================
            */

            recognition.addEventListener(
                "error",
                function (event) {

                    console.error(
                        "VOICE ERROR:",
                        event.error
                    );


                    voiceButton.innerHTML =
                        "🎤 Veles";


                    voiceButton.classList.remove(
                        "voice-active"
                    );


                    if (
                        event.error ===
                        "not-allowed"
                    ) {

                        alert(
                            "Veles nema dozvolu za mikrofon."
                        );

                    }

                }
            );

        }


        /*
        ==========================================
        AUTO SCROLL CHAT
        ==========================================
        */

        const chatWindow =
            document.getElementById(
                "chat-window"
            );


        if (chatWindow) {

            chatWindow.scrollTop =
                chatWindow.scrollHeight;

        }


    }
);