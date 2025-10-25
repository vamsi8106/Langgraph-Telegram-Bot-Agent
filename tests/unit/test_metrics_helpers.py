from app.metrics import observe, inc, HANDLER_LAT, TG_UPDATES

def test_observe_and_inc_do_not_crash():
    # With no active OTel span, exemplar path should be safe
    observe(HANDLER_LAT, 0.123, handler="unit")
    inc(TG_UPDATES, type="unit")
