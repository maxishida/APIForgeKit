from core.blueprint_generator import generate_nextjs_blueprint


def test_blueprint_generator_includes_nextjs_prisma_structure_without_full_code():
    blueprint = generate_nextjs_blueprint()

    assert "Next.js Blueprint — Lead Score Implementation" in blueprint
    assert "prisma/schema.prisma" in blueprint
    assert "/lib/prisma.ts" in blueprint
    assert "/lib/lead-score.ts" in blueprint
    assert "/app/api/leads/route.ts" in blueprint
    assert "/components/dashboard/LeadScoreChart.tsx" in blueprint
    assert "Não gerar código completo" in blueprint
