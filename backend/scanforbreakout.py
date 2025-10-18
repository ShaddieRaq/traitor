from app.tasks.trading_tasks import scan_for_breakouts

print('🚀 Triggering breakout scan...\n')

result = scan_for_breakouts(create_bots=True, min_confidence='MEDIUM')

print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print('🎯 BREAKOUT SCAN RESULTS:')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

# Check for error status
if result.get('status') == 'error':
    print(f"❌ SCAN FAILED: {result.get('error', 'Unknown error')}")
    print(f"  Breakouts detected: {result.get('breakouts_detected', 0)}")
    print(f"  Bots created: {result.get('bots_created', 0)}")
else:
    # Success - show all results
    print(f"  Breakouts detected: {result.get('breakouts_detected', 0)}")
    print(f"  After USD filter: {result.get('filtered_by_confidence', 'N/A')}")
    print(f"  New opportunities: {result.get('new_opportunities', 0)}")
    print(f"  Bots created: {result.get('bots_created', 0)}")
    print(f"  Bots resurrected: {result.get('bots_resurrected', 0)}")

    if result.get('created_bots'):
        print('\n✅ CREATED BOTS:')
        for bot in result['created_bots']:
            print(f"  - {bot['product_id']}: Score {bot['score']}, {bot['confidence']} confidence")

    if result.get('resurrected_bots'):
        print('\n♻️  RESURRECTED BOTS:')
        for bot in result['resurrected_bots']:
            print(f"  - {bot['product_id']}: Score {bot['score']}, {bot['confidence']} confidence")

print('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
