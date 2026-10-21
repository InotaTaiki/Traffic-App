import React from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, radius, space, type } from '../theme';

interface Props {
  from: string;
  to: string;
  onChangeFrom: (v: string) => void;
  onChangeTo: (v: string) => void;
  onSwap: () => void;
  onSubmit?: () => void; // called when the user presses Enter
  startingPointRef?: React.Ref<React.ElementRef<typeof TextInput>>;
}

export function SearchCard({
  from, to, onChangeFrom, onChangeTo, onSwap, onSubmit, startingPointRef,
}: Props) {
  return (
    <View style={styles.card}>
      <View style={styles.rail}>
        <View style={styles.originDot} />
        <View style={styles.railLine} />
        <View style={styles.destSquare} />
      </View>

      <View style={{ flex: 1 }}>
        <TextInput
          ref={startingPointRef}
          value={from} onChangeText={onChangeFrom} onSubmitEditing={onSubmit} returnKeyType="search"
          placeholder="Starting point (address)" placeholderTextColor={colors.inkSoft}
          style={styles.input} accessibilityLabel="Starting location address"
        />
        <View style={styles.divider} />
        <TextInput
          value={to} onChangeText={onChangeTo} onSubmitEditing={onSubmit} returnKeyType="search"
          placeholder="Where to? (address)" placeholderTextColor={colors.inkSoft}
          style={styles.input} accessibilityLabel="Destination"
        />
      </View>

      <Pressable onPress={onSwap} style={styles.swap} accessibilityLabel="Swap start and destination">
        <Text style={styles.swapText}>⇅</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.paper,
    borderRadius: radius.lg, paddingVertical: space.sm, paddingHorizontal: space.lg,
    elevation: 6, shadowColor: colors.ink, shadowOpacity: 0.15, shadowRadius: 12, shadowOffset: { width: 0, height: 4 },
  },
  rail: { alignItems: 'center', marginRight: space.md },
  originDot: { width: 12, height: 12, borderRadius: 6, borderWidth: 3, borderColor: colors.bay },
  railLine: { width: 2, height: 22, backgroundColor: colors.fog, marginVertical: 3 },
  destSquare: { width: 12, height: 12, backgroundColor: colors.orange, borderRadius: 2 },
  input: { ...type.body, color: colors.ink, paddingVertical: 11 },
  divider: { height: 1, backgroundColor: colors.fog },
  swap: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.fog, alignItems: 'center', justifyContent: 'center', marginLeft: space.sm },
  swapText: { fontSize: 18, color: colors.ink },
});