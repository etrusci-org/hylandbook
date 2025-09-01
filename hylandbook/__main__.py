import sys
import hylandbook.core



try:
    HB: hylandbook.core.Hylandbook = hylandbook.core.Hylandbook()
    HB.main()

except Exception as e:
    print(f"[BOO] {e}")
    input("press [Enter] to exit")
    sys.exit(10)

except KeyboardInterrupt:
    sys.exit(0)
