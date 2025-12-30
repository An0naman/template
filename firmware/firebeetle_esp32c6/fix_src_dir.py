Import("env")

# Override PROJECT_SRC_DIR to point to 'main' instead of 'src'
# This prevents the "two different targets" error in ESP-IDF builds
env.Replace(PROJECT_SRC_DIR=env.subst("$PROJECT_DIR/main"))
print("PROJECT_SRC_DIR overridden to:", env.subst("$PROJECT_SRC_DIR"))
