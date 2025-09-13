import hylandbook.app




try:
    App = hylandbook.app.App()
    App.main()
except KeyboardInterrupt:
    pass
except Exception as e:
    print(f"\nsomething went wrong: {e}")
