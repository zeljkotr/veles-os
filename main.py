from core.brain import ask_veles
from core.memory.memory import remember
from services.voice.speak import speak


VOICE_OUTPUT_ENABLED = True


print("====================")
print("     VELES ONLINE")
print("====================")


while True:

    question = input("\nYOU: ")

    if question.lower() in ["exit", "quit"]:
        print("VELES offline.")
        break

    result = ask_veles(question)

    print("\nVELES:")
    print(result["answer"])

    if VOICE_OUTPUT_ENABLED:
        try:
            speak(result["answer"])
        except Exception as e:
            print(f"[VELES] Voice output failed: {e}")

    suggestion = result.get("suggested_memory")

    if suggestion:
        confirm = input(
            f"\n[VELES suggests remembering: "
            f"{suggestion['key']} = {suggestion['value']}] "
            f"Save? (yes/no): "
        ).strip().lower()

        if confirm == "yes":
            remember(suggestion["key"], suggestion["value"])
            print("Saved.")