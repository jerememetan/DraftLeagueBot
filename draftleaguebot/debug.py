# defines whether it should show any debugs
def should_debug(enabled, debug_turns, battle):
    if not enabled:
        return False
    turn = getattr(battle, "turn", None)
    if turn is None:
        return True
    return turn <= debug_turns

# logger for moves calculated and shows scoring of moves
def log_decision(battle, slot_index, attacker, scored):
    turn = getattr(battle, "turn", "?")
    attacker_name = getattr(attacker, "name", "?")
    sorted_scored = sorted(scored, key=lambda item: item[0], reverse=True)
    top_moves = sorted_scored[:3]
    top_str = " | ".join(
        f"{getattr(move, 'id', '?')}->{getattr(target, 'name', '?')} ({score:.2f})"
        for score, move, target in top_moves
    )
    print(
        f"[AI DEBUG] turn={turn} slot={slot_index} attacker={attacker_name} "
        f"top_candidates=[{top_str}]"
    )

# logger for final move selected
def log_final_orders(orders):
    messages = [order.message for order in orders]
    print(f"[AI DEBUG] final_orders={messages}")
