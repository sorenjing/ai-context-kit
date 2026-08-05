# Security policy

Do not open a public issue for a vulnerability that could expose local files, secrets, or paths outside the configured workspace. Report it privately through GitHub's security advisory feature for this repository.

AI Context Kit is designed to operate offline. Unexpected network activity, traversal outside the resolved workspace, symlink traversal, or reading common secret files should be treated as security bugs.

