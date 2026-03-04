def explain_step(state) -> str:
    lines = []

    before = state.metadata["snapshots"]["before"]
    after = state.metadata["snapshots"]["after"]
    rule_effects = state.metadata["rule_effects"]
    reasons = state.metadata.get("rule_reasons", {})

    for pollutant in before:
        delta = after[pollutant] - before[pollutant]
        if abs(delta) < 0.01:
            continue

        lines.append(
            f"{pollutant.upper()} changed by {delta:+.2f} "
            f"({before[pollutant]:.2f} → {after[pollutant]:.2f})"
        )

        for rule, value in rule_effects.get(pollutant, {}).items():
            lines.append(f"  └─ {rule}: {value:+.2f}")

    if "temperature_ozone_effect" in reasons:
        r = reasons["temperature_ozone_effect"]

        delta_t = r.get("delta_temperature")
        solar = r.get("solar_potential")
        driving = r.get("ozone_driving_factor")

        if delta_t is not None and solar is not None:
            lines.append(
            f"O₃ formation driven by ΔT={delta_t}°C "
            f"and solar potential={solar} "
            f"(driving={driving})"
            )
        else:
            lines.append("O₃ formation rule applied")

    return "\n".join(lines)
