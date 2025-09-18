import hylandbook.app
import hylandbook.screen




try:
    App = hylandbook.app.App()
    App.main()
except KeyboardInterrupt:
    pass
except Exception as e:
    print(f"\nsomething went wrong: {e}")
    hylandbook.screen.Screen.prompt_to_exit(10)
