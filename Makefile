MOSFHET_DIR = ./src/mosfhet
BUILD_DIR = ./build
include $(MOSFHET_DIR)/Makefile.def
INCLUDE_DIRS += ./include/
INCLUDE_FLAGS = $(addprefix -I, $(INCLUDE_DIRS))
KEY=BINARY
PARAM=SET_2_3

SRC = sparse_amortized_bootstrap.c sab_profile.c
ifeq ($(ENABLE_PVW_TMLWE),true)
	SRC += sab_pvw.c
endif
ifeq ($(SAB_OPERATOR_EQUIV_TEST),true)
	SRC += sab_operator.c
endif
SRC_SELF = $(addprefix ./src/, $(SRC))
OBJ_SELF = $(addprefix $(BUILD_DIR)/, $(notdir $(SRC_SELF:.c=.o)))

# Get mosfhet object files - all in build directory
# Need to handle subdirectories in source paths
OBJ_MOSFHET = $(addprefix $(BUILD_DIR)/, $(notdir $(__SRC:.c=.o)))
OBJ_MOSFHET := $(OBJ_MOSFHET:.s=.o)

.PHONY: all clean setup

all: main

# Setup: create build directory
setup:
	mkdir -p $(BUILD_DIR)

# Compile project objects to build directory
$(BUILD_DIR)/%.o: ./src/%.c | setup
	$(CC) -g -c $(OPT_FLAGS) $(INCLUDE_FLAGS) -D$(KEY) -D$(PARAM) $< -o $@

# Compile main.o to build directory
$(BUILD_DIR)/main.o: main.c | setup
	$(CC) -g -c $(OPT_FLAGS) $(INCLUDE_FLAGS) -D$(KEY) -D$(PARAM) $< -o $@

# Compile mosfhet objects to build directory - handle subdirectories
$(BUILD_DIR)/keyswitch.o: $(MOSFHET_DIR)/src/keyswitch.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/bootstrap.o: $(MOSFHET_DIR)/src/bootstrap.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/bootstrap_ga.o: $(MOSFHET_DIR)/src/bootstrap_ga.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/tlwe.o: $(MOSFHET_DIR)/src/tlwe.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/trlwe.o: $(MOSFHET_DIR)/src/trlwe.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/trgsw.o: $(MOSFHET_DIR)/src/trgsw.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/misc.o: $(MOSFHET_DIR)/src/misc.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/polynomial.o: $(MOSFHET_DIR)/src/polynomial.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/register.o: $(MOSFHET_DIR)/src/register.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/pvwtlwe.o: $(MOSFHET_DIR)/src/pvwtlwe.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/pvwtmlwe.o: $(MOSFHET_DIR)/src/pvwtmlwe.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/mattrgsw.o: $(MOSFHET_DIR)/src/mattrgsw.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/fips202.o: $(MOSFHET_DIR)/src/sha3/fips202.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/karatsuba.o: $(MOSFHET_DIR)/src/fft/karatsuba.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/ffnt.o: $(MOSFHET_DIR)/src/fft/ffnt/ffnt.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/aes_rng.o: $(MOSFHET_DIR)/src/rnd/aes_rng.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/spqlios-fft-fma.o: $(MOSFHET_DIR)/src/fft/spqlios/spqlios-fft-fma.s | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/spqlios-ifft-fma.o: $(MOSFHET_DIR)/src/fft/spqlios/spqlios-ifft-fma.s | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/spqlios-fft-impl.o: $(MOSFHET_DIR)/src/fft/spqlios/spqlios-fft-impl.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/spqlios-fft-avx512.o: $(MOSFHET_DIR)/src/fft/spqlios/spqlios-fft-avx512.s | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/spqlios-ifft-avx512.o: $(MOSFHET_DIR)/src/fft/spqlios/spqlios-ifft-avx512.s | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/spqlios-fft-impl-avx512.o: $(MOSFHET_DIR)/src/fft/spqlios/spqlios-fft-impl-avx512.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

$(BUILD_DIR)/fft_processor_spqlios.o: $(MOSFHET_DIR)/src/fft/spqlios/fft_processor_spqlios.c | setup
	$(CC) -g -c $(LIB_FLAGS) $(INCLUDE_FLAGS) $< -o $@

# Link all objects
main: $(OBJ_MOSFHET) $(OBJ_SELF) $(BUILD_DIR)/main.o
	$(CC) -g -o main $^ $(LIBS) -lm

clean:
	rm -rf $(BUILD_DIR) main
