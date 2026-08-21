# PATH: fix_stage9_joint_owner_visibility.py
# STAGE 9 -- Recovery drops every joint owner except the alphabetically-first one
# Run from project root: py fix_stage9_joint_owner_visibility.py
#
# CONTEXT / WHAT WAS ACTUALLY VERIFIED
# -------------------------------------------------------------------------
# RecoveryController.buildOwnerTasks() builds one Recovery card per PERSON,
# pulling in every project that person owes on. For a project with multiple
# owners (proprietors), the code picked exactly one "primary" owner --
# whoever's fullName sorts first alphabetically -- and attached that
# project's balance only to that person's card:
#
#     Client primary = proprietors.stream()
#             .sorted(Comparator.comparing(Client::getFullName))
#             .findFirst().orElse(null);
#
#     if (primary != null) {
#         clientPlotsMap.computeIfAbsent(primary.getId(), k -> new ArrayList<>()).add(plot);
#         clientRegistry.put(primary.getId(), primary);
#     }
#
# Every OTHER co-owner on that project got no card entry for it at all,
# unless they separately happened to be the sole/primary owner of some other
# project. Staff working the Recovery queue would never see that project, or
# its balance, listed under a co-owner who didn't win the alphabetical draw.
# If that co-owner also had their own solo projects, their on-screen "total
# demand" understated their real exposure too.
#
# THE FIX
# -------------------------------------------------------------------------
# Attach each project to EVERY proprietor instead of picking one "primary".
# Each co-owner now gets their own Recovery card entry for it, in addition
# to whatever solo or other-joint projects they already carry, and their
# totalDemand correctly sums across all of them.
#
# No DTO or schema changes needed -- RecoveryTaskDTO already models one
# card = one person with a list of plots. Per-person cooldown state
# (lastContactedAt / monthlyContactCount) is untouched by this change: it
# already lives on Client (not per-project, not per-ownership-pairing), so
# it is naturally shared and consistent across every project a person
# co-owns -- confirmed directly in Client.java, unaffected here.
#
# Safe to re-run: the patch is checked before writing; if the target is not
# found it prints MISSING and leaves the file alone (most likely meaning
# this stage is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def patch(label, rel_path, old, new):
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        print("[STAGE 9] " + label + " ... MISSING (file not found: " + rel_path + ")")
        return False
    content = read_file(full_path)
    if old not in content:
        if new in content:
            print("[STAGE 9] " + label + " ... OK (already applied)")
            return True
        print("[STAGE 9] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        return False
    content = content.replace(old, new, 1)
    write_file(full_path, content)
    print("[STAGE 9] " + label + " ... OK")
    return True


def main():
    print("=" * 70)
    print("STAGE 9 -- joint-owner visibility gap in Recovery (backend only)")
    print("=" * 70)

    ok = 0
    total = 0

    total += 1
    ok += patch(
        "RecoveryController.buildOwnerTasks: attach each project to every "
        "proprietor, instead of only the alphabetically-first 'primary' owner",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java",

        "            Set<Client> proprietors = plot.getProprietors();\n"
        "            if (proprietors == null || proprietors.isEmpty()) continue;\n"
        "\n"
        "            Client primary = proprietors.stream()\n"
        "                    .sorted(Comparator.comparing(Client::getFullName))\n"
        "                    .findFirst().orElse(null);\n"
        "\n"
        "            if (primary != null) {\n"
        "                clientPlotsMap.computeIfAbsent(primary.getId(), k -> new ArrayList<>()).add(plot);\n"
        "                clientRegistry.put(primary.getId(), primary);\n"
        "            }\n"
        "        }",

        "            Set<Client> proprietors = plot.getProprietors();\n"
        "            if (proprietors == null || proprietors.isEmpty()) continue;\n"
        "\n"
        "            // STAGE 9 FIX: NIN_JOINT_OWNER_VISIBILITY\n"
        "            // Previously only the alphabetically-first co-owner (\"primary\") got\n"
        "            // this project attached to their Recovery card, so every other joint\n"
        "            // owner's exposure on this project was invisible to Recovery entirely.\n"
        "            // Attach the project to EVERY proprietor instead -- each co-owner gets\n"
        "            // their own card entry for it, on top of whatever solo/other-joint\n"
        "            // projects they carry. Per-person state (lastContactedAt /\n"
        "            // monthlyContactCount cooldown clock) is unaffected by this change: it\n"
        "            // already lives on Client, so it's naturally shared/consistent across\n"
        "            // every project that person co-owns.\n"
        "            for (Client proprietor : proprietors) {\n"
        "                if (proprietor == null) continue;\n"
        "                clientPlotsMap.computeIfAbsent(proprietor.getId(), k -> new ArrayList<>()).add(plot);\n"
        "                clientRegistry.put(proprietor.getId(), proprietor);\n"
        "            }\n"
        "        }",
    )

    print("-" * 70)
    print(str(ok) + "/" + str(total) + " patches applied")
    if ok < total:
        print("Some patches were MISSING -- review output above before committing.")


if __name__ == "__main__":
    main()