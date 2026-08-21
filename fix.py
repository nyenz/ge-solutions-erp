# PATH: fix_stage8_nin_edit_bypass.py
# STAGE 8 -- close the real NIN_NAME_MISMATCH gap on the Edit path
# Run from project root: py fix_stage8_nin_edit_bypass.py
#
# CONTEXT / WHAT WAS ACTUALLY VERIFIED
# -------------------------------------------------------------------------
# The brief that kicked this session off ("Issue #1") claimed the mismatch
# popup from Intake was never wired into the Edit screen at all. That claim
# does NOT hold up against the code as of commit 27223e7 ("Stage 3: NIN
# name-mismatch guard, soft-delete/restore"):
#
#   - erp-frontend/src/pages/DigitalFolder/FolderPage.jsx already has its own
#     ninMismatch state, its own handleNinBlurCheck() (calls
#     clientService.lookupNin on blur, same as Intake), its own
#     handleNinMismatchConfirm/Reject, its own <NinMismatchModal /> render,
#     and its own save-time guard inside handleCommit():
#         if (ninMismatch) { toast(...); return; }
#     This mirrors IntakePage.jsx almost line for line. The frontend is NOT
#     the gap.
#
# The REAL gap is one layer down, on the backend, and it is a genuine bug:
#
#   - LandService.atomicIntake() (Intake / create) routes every owner
#     through ClientService.findOrCreateClientByNin(), which is the ONE
#     place NIN_NAME_MISMATCH is actually thrown, and which never renames an
#     existing matching Client -- it just returns the record as-is.
#
#   - LandService.updateProjectFull() (Edit / the "full-update" endpoint)
#     instead did:
#         clientRepository.findByNationalId(normalizedNin)
#             .orElseGet(() -> clientService.findOrCreateClientByNin(...))
#     i.e. it only calls the mismatch-checking method on the NOT-FOUND
#     branch (a brand-new NIN). For an EXISTING NIN -- the exact scenario
#     the brief is worried about -- it skips the check entirely and then
#     unconditionally runs:
#         person.setFullName(incoming.getFullName().toUpperCase());
#     silently renaming that person's identity record, which is shared
#     across every project they're on.
#
# The frontend's blocking modal is a real, working safety net for the normal
# click-path through the UI -- but it's advisory only, driven by a separate
# GET lookupNin call. It does nothing to stop a request that reaches
# PUT /land/projects/{id}/full-update by any other route (a race between two
# staff editing the same NIN at once, a retried/replayed request after the
# blur check already fired once, a future frontend regression, a direct API
# call). Intake has a hard backend backstop for this; Edit did not.
#
# THE FIX
# -------------------------------------------------------------------------
# Route updateProjectFull() through the exact same
# ClientService.findOrCreateClientByNin() call Intake uses, unconditionally,
# for every owner -- so the NIN_NAME_MISMATCH guard is enforced identically
# on both paths, and an existing person's fullName is never rewritten by
# this method (matching Intake behavior: full name is identity-level, only
# ever changed by whatever explicit process the business decides, not by a
# routine per-project edit). Per-project fields (email/phone/home address)
# remain editable exactly as before.
#
# No frontend change needed. NinMismatchModal.jsx, IntakePage.jsx, and
# FolderPage.jsx are unchanged and already correct.
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
        print("[STAGE 8] " + label + " ... MISSING (file not found: " + rel_path + ")")
        return False
    content = read_file(full_path)
    if old not in content:
        if new in content:
            print("[STAGE 8] " + label + " ... OK (already applied)")
            return True
        print("[STAGE 8] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        return False
    content = content.replace(old, new, 1)
    write_file(full_path, content)
    print("[STAGE 8] " + label + " ... OK")
    return True


def main():
    print("=" * 70)
    print("STAGE 8 -- NIN_NAME_MISMATCH guard was bypassed on Edit (backend only)")
    print("=" * 70)

    ok = 0
    total = 0

    total += 1
    ok += patch(
        "LandService.updateProjectFull: route owners through findOrCreateClientByNin "
        "unconditionally, instead of only on the not-found branch",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",

        "        if (request.getOwners() != null) {\n"
        "            Set<Client> updatedRegistry = new HashSet<>();\n"
        "            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {\n"
        "                if (incoming.getNationalId() == null || incoming.getNationalId().isBlank()) {\n"
        "                    throw new BusinessException(\"NIN_REQUIRED: Owner \\\"\" + incoming.getFullName() + \"\\\" is missing a National ID (NIN).\");\n"
        "                }\n"
        "                String normalizedNin = incoming.getNationalId().trim().toUpperCase();\n"
        "                Client person = clientRepository.findByNationalId(normalizedNin)\n"
        "                        .orElseGet(() -> clientService.findOrCreateClientByNin(\n"
        "                                incoming.getFullName(), normalizedNin, incoming.getPhone(), incoming.getEmail()));\n"
        "                person.setFullName(incoming.getFullName().toUpperCase());\n"
        "                person.setNationalId(normalizedNin);\n"
        "                person.setEmail(incoming.getEmail() != null\n"
        "                        ? incoming.getEmail().toLowerCase() : null);\n"
        "                person.setHomeAddress(incoming.getAddress());\n"
        "                if (incoming.getPhone() != null && !incoming.getPhone().isBlank()) {\n"
        "                    person.setPhoneNumber(incoming.getPhone());\n"
        "                }\n"
        "                clientRepository.save(person);\n"
        "                updatedRegistry.add(person);\n"
        "            }\n"
        "            project.setProprietors(updatedRegistry);\n"
        "        }",

        "        if (request.getOwners() != null) {\n"
        "            Set<Client> updatedRegistry = new HashSet<>();\n"
        "            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {\n"
        "                if (incoming.getNationalId() == null || incoming.getNationalId().isBlank()) {\n"
        "                    throw new BusinessException(\"NIN_REQUIRED: Owner \\\"\" + incoming.getFullName() + \"\\\" is missing a National ID (NIN).\");\n"
        "                }\n"
        "                // STAGE 8 FIX: this used to look the client up directly by NIN and,\n"
        "                // when found, unconditionally overwrite its stored fullName with\n"
        "                // whatever was typed on this form -- bypassing the NIN_NAME_MISMATCH\n"
        "                // guard entirely, because that guard only ran inside\n"
        "                // findOrCreateClientByNin(), which this code only called on the\n"
        "                // NOT-FOUND branch (orElseGet). Reusing an existing NIN with a\n"
        "                // different typed name silently renamed that person's identity\n"
        "                // record everywhere they appear. Routing every owner through\n"
        "                // findOrCreateClientByNin() unconditionally -- same as atomicIntake\n"
        "                // does on Intake -- restores the mismatch check on Edit, and, like\n"
        "                // Intake, leaves fullName untouched for a matching existing person\n"
        "                // (full name is identity-level, not a per-project field; it only\n"
        "                // changes via the explicit mismatch-confirmation flow).\n"
        "                Client person = clientService.findOrCreateClientByNin(\n"
        "                        incoming.getFullName(), incoming.getNationalId(), incoming.getPhone(), incoming.getEmail());\n"
        "                person.setEmail(incoming.getEmail() != null\n"
        "                        ? incoming.getEmail().toLowerCase() : null);\n"
        "                person.setHomeAddress(incoming.getAddress());\n"
        "                if (incoming.getPhone() != null && !incoming.getPhone().isBlank()) {\n"
        "                    person.setPhoneNumber(incoming.getPhone());\n"
        "                }\n"
        "                clientRepository.save(person);\n"
        "                updatedRegistry.add(person);\n"
        "            }\n"
        "            project.setProprietors(updatedRegistry);\n"
        "        }",
    )

    print("-" * 70)
    print(str(ok) + "/" + str(total) + " patches applied")
    if ok < total:
        print("Some patches were MISSING -- review output above before committing.")


if __name__ == "__main__":
    main()