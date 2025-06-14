import traceback

def managed_main_execution(main_fun:callable):
    try:
        main_fun()
    except Exception as e:
        print()
        print('⛔⛔ ERROR ⛔⛔')
        print()
        print(f'⛔  {traceback.format_exc().rstrip()}')
        print()
        print('⛔ Error Type:')
        print(f'  {type(e).__name__}')
        print()
        print('⛔ Error Summary:')
        print(f'  {str(e).rstrip()}')
        exit(1)
