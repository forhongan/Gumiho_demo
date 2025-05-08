import logging

def b_test():
    try:
        print("b_test")
        logging.info("b_test")
    except Exception as e:
        logging.error(f"b_test error: {str(e)}")