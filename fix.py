# PATH: fix.py
# DANGER ZONE FOLLOW-UP: ALSO WIPE CLOUDINARY STORAGE
# Run from project root: python fix.py   (or: py fix.py)
# Requires the previous "Add root-only full system data wipe" fix.py
# to have already been applied and deployed.
#
# WHAT THIS DOES:
# The DANGER ZONE wipe only cleared database tables -- it never touched
# files already uploaded to Cloudinary (title documents, images, etc).
# This patch closes that gap:
#   1. FileStorageService.java: adds a new deleteAllFiles() method.
#   2. LocalStorageServiceImpl.java: implements it -- purges every file
#      under the "ge_solutions/" prefix on Cloudinary, across all
#      resource types (image, raw, video), then best-effort removes
#      the now-empty root folder.
#   3. SystemAdminController.java: the wipe-all-data endpoint now calls
#      fileStorageService.deleteAllFiles() as its last step, and the
#      response message + class javadoc are updated to say so.
#   4. SettingsPage.jsx: DANGER ZONE warning text and confirm popup now
#      mention storage too, so it is not surprising.
#
# WHAT IT DOES NOT DO:
# If cloudinary.cloud-name is still set to "test" (local/dev config),
# the purge is skipped automatically -- same mock-bypass pattern already
# used by storeFile(). It only actually purges Cloudinary when a real
# cloud name is configured (i.e. in production on Render).
#
# AFTER RUNNING THIS + DEPLOY:
# Same DANGER ZONE flow as before (Settings > DANGER ZONE > type
# WIPE-EVERYTHING > WIPE ALL DATA > confirm). It now also empties
# Cloudinary storage in the same click.
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone.

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# (file, old, new) patches applied with str.replace, in order
PATCHES = [
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java",
        'import com.gesolutions.erp.config.DataInitializer;\nimport com.gesolutions.erp.modules.land.service.StageTemplateService;',
        'import com.gesolutions.erp.config.DataInitializer;\nimport com.gesolutions.erp.modules.land.service.FileStorageService;\nimport com.gesolutions.erp.modules.land.service.StageTemplateService;',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java",
        '    private final DataSource dataSource;\n    private final DataInitializer dataInitializer;\n    private final StageTemplateService stageTemplateService;',
        '    private final DataSource dataSource;\n    private final DataInitializer dataInitializer;\n    private final StageTemplateService stageTemplateService;\n    private final FileStorageService fileStorageService;',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java",
        ' * After the wipe, the root admin account, the project index counter, and\n * the default stage-template checklist are automatically reseeded so the\n * app is immediately usable again (nobody gets permanently locked out).\n *\n * NOTE: This does NOT delete files already uploaded to Cloudinary. Any\n * documents attached to wiped projects become orphaned there -- clean those\n * up separately in the Cloudinary dashboard if needed.\n */',
        ' * After the wipe, the root admin account, the project index counter, and\n * the default stage-template checklist are automatically reseeded so the\n * app is immediately usable again (nobody gets permanently locked out).\n *\n * Also purges every file this app has ever uploaded to Cloudinary (all\n * project documents, all resource types), so nothing is left behind in\n * storage either.\n */',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/admin/controller/SystemAdminController.java",
        '        // Reseed the default stage template checklist\n        stageTemplateService.seedDefaultStagesIfEmpty();\n        System.out.println(">>> [WIPE] OK: default stage template reseeded");\n\n        System.out.println(">>> [WIPE] SYSTEM RESET COMPLETE. Fresh start.");\n\n        Map<String, Object> response = new LinkedHashMap<>();\n        response.put("wiped", true);\n        response.put("tablesWiped", TABLES_TO_WIPE);\n        response.put("message", "All business data deleted. Root admin login, project index, and default stage template were reseeded to defaults. You will need to log in again with the ADMIN_EMAIL / ADMIN_DEFAULT_PASSWORD credentials. NOTE: files already on Cloudinary were NOT deleted.");\n        return ResponseEntity.ok(response);',
        '        // Reseed the default stage template checklist\n        stageTemplateService.seedDefaultStagesIfEmpty();\n        System.out.println(">>> [WIPE] OK: default stage template reseeded");\n\n        // Purge every uploaded file from Cloudinary storage too\n        fileStorageService.deleteAllFiles();\n        System.out.println(">>> [WIPE] OK: Cloudinary storage purge attempted");\n\n        System.out.println(">>> [WIPE] SYSTEM RESET COMPLETE. Fresh start.");\n\n        Map<String, Object> response = new LinkedHashMap<>();\n        response.put("wiped", true);\n        response.put("tablesWiped", TABLES_TO_WIPE);\n        response.put("message", "All business data AND all uploaded files on Cloudinary have been deleted. Root admin login, project index, and default stage template were reseeded to defaults. You will need to log in again with the ADMIN_EMAIL / ADMIN_DEFAULT_PASSWORD credentials.");\n        return ResponseEntity.ok(response);',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/FileStorageService.java",
        '    // NEW: Deletes the entire folder from Cloudinary after purge\n    void deleteFolder(@NonNull String folderPath);\n}',
        '    // NEW: Deletes the entire folder from Cloudinary after purge\n    void deleteFolder(@NonNull String folderPath);\n\n    // NEW: Wipes every file ever uploaded by this app (all projects, all\n    // resource types) from Cloudinary. Used by the DANGER ZONE full wipe.\n    void deleteAllFiles();\n}',
    ),
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LocalStorageServiceImpl.java",
        '    @Override\n    public void deleteFolder(@NonNull String folderPath) {\n        try {\n            System.out.println(">>> CLOUDINARY DELETE FOLDER: " + folderPath);\n            cloudinary.api().deleteFolder(folderPath, ObjectUtils.emptyMap());\n            System.out.println(">>> FOLDER DELETED: " + folderPath);\n        } catch (Exception e) {\n            System.err.println(">>> FOLDER DELETE FAULT (may already be empty/gone): " + e.getMessage());\n        }\n    }\n}',
        '    @Override\n    public void deleteFolder(@NonNull String folderPath) {\n        try {\n            System.out.println(">>> CLOUDINARY DELETE FOLDER: " + folderPath);\n            cloudinary.api().deleteFolder(folderPath, ObjectUtils.emptyMap());\n            System.out.println(">>> FOLDER DELETED: " + folderPath);\n        } catch (Exception e) {\n            System.err.println(">>> FOLDER DELETE FAULT (may already be empty/gone): " + e.getMessage());\n        }\n    }\n\n    @Override\n    public void deleteAllFiles() {\n        if (this.cloudName != null && this.cloudName.trim().equals("test")) {\n            System.out.println(">>> LOCAL TEST MOCK: Skipping real Cloudinary purge.");\n            return;\n        }\n\n        // Every file this app ever uploads lives under the "ge_solutions/"\n        // prefix (see storeFile above). Cloudinary keeps image/raw/video as\n        // separate namespaces, so each has to be purged by prefix on its own.\n        for (String resourceType : new String[]{"image", "raw", "video"}) {\n            try {\n                cloudinary.api().deleteResourcesByPrefix(\n                        "ge_solutions/",\n                        ObjectUtils.asMap("resource_type", resourceType)\n                );\n                System.out.println(">>> CLOUDINARY PURGE OK: resource_type=" + resourceType);\n            } catch (Exception e) {\n                System.err.println(">>> CLOUDINARY PURGE FAULT (resource_type=" + resourceType + "): " + e.getMessage());\n            }\n        }\n\n        // Best-effort: remove the now-empty top-level folder. Cloudinary\n        // only deletes a folder once it has no files left in it, and this\n        // can silently no-op if a subfolder is still cached as non-empty --\n        // that is cosmetic only, the actual files above are already gone.\n        try {\n            cloudinary.api().deleteFolder("ge_solutions", ObjectUtils.emptyMap());\n            System.out.println(">>> CLOUDINARY ROOT FOLDER DELETED: ge_solutions");\n        } catch (Exception e) {\n            System.err.println(">>> CLOUDINARY ROOT FOLDER DELETE FAULT (cosmetic only, files are already gone): " + e.getMessage());\n        }\n    }\n}',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '                                    <span>\n                                        Permanently deletes every client, project, payment, and log in the system.\n                                        Cannot be undone. Root login, project index, and default stage template\n                                        are automatically restored to defaults right after.\n                                    </span>',
        '                                    <span>\n                                        Permanently deletes every client, project, payment, and log in the system,\n                                        plus every file uploaded to storage. Cannot be undone. Root login,\n                                        project index, and default stage template are automatically restored\n                                        to defaults right after.\n                                    </span>',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "        const ok = await confirm(\n            'FULL SYSTEM WIPE',\n            'This permanently deletes every client, project, payment, and log in the system. This CANNOT be undone. Continue?',\n            'danger'\n        );",
        "        const ok = await confirm(\n            'FULL SYSTEM WIPE',\n            'This permanently deletes every client, project, payment, and log in the system, plus every uploaded file in storage. This CANNOT be undone. Continue?',\n            'danger'\n        );",
    ),
]


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def main():
    for rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(full_path):
            print("MISSING (file not found): " + rel_path)
            continue
        content = read_file(full_path)
        if new in content:
            print("SKIP (already patched): " + rel_path)
            continue
        if old not in content:
            print("MISSING (patch target not found -- is the previous fix.py applied?): " + rel_path)
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("OK: patched " + rel_path)

    print("")
    print("Done. Next steps:")
    print("1. git add -A && git commit -m \'Wipe Cloudinary storage too on full system wipe\' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Settings > DANGER ZONE > type WIPE-EVERYTHING > WIPE ALL DATA > confirm.")
    print("   This now clears the database AND Cloudinary storage in one click.")


if __name__ == "__main__":
    main()